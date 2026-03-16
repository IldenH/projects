#!/usr/bin/env python3
"""Offline behavior cloning trainer for Grocery Bot using replay data.

Trains the same Tianshou Net architecture used by `tianshou_bot.py` and saves
`{"model": state_dict}` checkpoints compatible with `TS_CHECKPOINT`.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import random
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from grocery_bot import GroceryPlanner
from tianshou_bot import ACTION_TO_ID, PolicyConfig, TianshouActionPolicy, TianshouGroceryBot


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_replay_file(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.loads(f.readline())


def collect_samples(replay_paths: List[Path]) -> Tuple[np.ndarray, np.ndarray, Counter]:
    # Keep separate planners per replay stream to preserve per-game memory dynamics.
    planner_for_heuristics = GroceryPlanner()

    dummy_policy = TianshouActionPolicy(PolicyConfig(checkpoint=None))
    bot_runtime = TianshouGroceryBot(dummy_policy)

    obs_rows: List[np.ndarray] = []
    targets: List[int] = []
    dist = Counter()

    for path in replay_paths:
        data = load_replay_file(path)
        trajectory = data.get("trajectory", [])

        for step in trajectory:
            state = step["state"]
            if state.get("round", 0) == 0:
                planner_for_heuristics.reset_for_new_game(state)
                bot_runtime.planner.reset_for_new_game(state)
            # Prefer expert labels if present (DAgger logs), fallback to executed actions.
            label_actions = step.get("expert_actions", step.get("actions", []))
            replay_actions = {a["bot"]: a for a in label_actions}

            heuristic_actions = planner_for_heuristics.decide_actions(state)
            heur_by_id = {a["bot"]: a for a in heuristic_actions}

            # Build context with same logic used by tianshou runtime.
            ctx = bot_runtime._build_context(state)

            for bot in sorted(state.get("bots", []), key=lambda b: b["id"]):
                bot_id = bot["id"]
                if bot_id not in replay_actions:
                    continue

                replay_action_name = replay_actions[bot_id].get("action", "wait")
                if replay_action_name not in ACTION_TO_ID:
                    continue

                heur_name = heur_by_id.get(bot_id, {"action": "wait"})["action"]
                obs = bot_runtime._obs(state, bot, ctx, heur_name)

                obs_rows.append(obs)
                action_id = ACTION_TO_ID[replay_action_name]
                targets.append(action_id)
                dist[replay_action_name] += 1

    if not obs_rows:
        raise RuntimeError("No training samples collected from replay files.")

    X = np.stack(obs_rows).astype(np.float32)
    y = np.asarray(targets, dtype=np.int64)
    return X, y, dist


def train_bc(
    X: np.ndarray,
    y: np.ndarray,
    policy: TianshouActionPolicy,
    epochs: int,
    batch_size: int,
    lr: float,
    val_split: float,
) -> Dict[str, float]:
    if policy.net is None:
        raise RuntimeError("Tianshou Net unavailable. Ensure tianshou is installed in your nix shell.")

    n = len(X)
    idx = np.arange(n)
    np.random.shuffle(idx)

    val_n = int(n * val_split)
    val_idx = idx[:val_n]
    train_idx = idx[val_n:]

    X_train = torch.from_numpy(X[train_idx])
    y_train = torch.from_numpy(y[train_idx])
    X_val = torch.from_numpy(X[val_idx]) if val_n > 0 else None
    y_val = torch.from_numpy(y[val_idx]) if val_n > 0 else None

    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)

    class_counts = np.bincount(y_train.numpy(), minlength=policy.cfg.action_dim).astype(np.float32)
    class_weights = class_counts.sum() / np.maximum(class_counts, 1.0)
    class_weights = class_weights / class_weights.mean()
    class_weights_t = torch.as_tensor(class_weights, dtype=torch.float32, device=policy.device)

    optimizer = torch.optim.Adam(policy.net.parameters(), lr=lr)

    best_val = float("inf")
    best_state = None

    for epoch in range(1, epochs + 1):
        policy.net.train()
        total_loss = 0.0
        total_correct = 0
        total_seen = 0

        for xb, yb in train_loader:
            xb = xb.to(policy.device)
            yb = yb.to(policy.device)

            logits, _ = policy.net(xb)
            loss = F.cross_entropy(logits, yb, weight=class_weights_t)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

            total_loss += float(loss.item()) * xb.size(0)
            pred = logits.argmax(dim=1)
            total_correct += int((pred == yb).sum().item())
            total_seen += xb.size(0)

        train_loss = total_loss / max(total_seen, 1)
        train_acc = total_correct / max(total_seen, 1)

        val_loss = 0.0
        val_acc = 0.0
        if val_n > 0:
            policy.net.eval()
            with torch.no_grad():
                xv = X_val.to(policy.device)
                yv = y_val.to(policy.device)
                v_logits, _ = policy.net(xv)
                v_loss = F.cross_entropy(v_logits, yv, weight=class_weights_t)
                val_loss = float(v_loss.item())
                val_acc = float((v_logits.argmax(dim=1) == yv).float().mean().item())

            if val_loss < best_val:
                best_val = val_loss
                best_state = {k: v.detach().cpu().clone() for k, v in policy.net.state_dict().items()}

        print(
            f"epoch {epoch:03d} | train_loss={train_loss:.4f} train_acc={train_acc:.4f}"
            + (f" | val_loss={val_loss:.4f} val_acc={val_acc:.4f}" if val_n > 0 else "")
        )

    if best_state is not None:
        policy.net.load_state_dict(best_state)

    metrics = {"train_acc": train_acc, "train_loss": train_loss}
    if val_n > 0:
        metrics.update({"val_acc": val_acc, "val_loss": val_loss})
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-dir", default="replays", help="Directory with *.json.gz replay files")
    parser.add_argument("--out", default="checkpoints/tianshou_bc.pt", help="Output checkpoint path")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--val-split", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default=os.getenv("TS_DEVICE", "cpu"))
    args = parser.parse_args()

    set_seed(args.seed)

    replay_dir = Path(args.replay_dir)
    replay_paths = sorted(replay_dir.glob("*.json.gz"))
    if not replay_paths:
        raise RuntimeError(f"No replay files found in {replay_dir}")

    print(f"Loading {len(replay_paths)} replay files...")
    X, y, dist = collect_samples(replay_paths)
    print(f"Samples: {len(X)}")
    print(f"Action distribution: {dict(dist)}")

    policy = TianshouActionPolicy(PolicyConfig(device=args.device, checkpoint=None))
    if policy.net is None:
        raise RuntimeError(f"Tianshou unavailable: {policy.import_error}")

    metrics = train_bc(
        X=X,
        y=y,
        policy=policy,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        val_split=args.val_split,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": policy.net.state_dict(),
            "meta": {
                "obs_dim": policy.cfg.obs_dim,
                "action_dim": policy.cfg.action_dim,
                "hidden_sizes": policy.cfg.hidden_sizes,
                "metrics": metrics,
                "samples": int(len(X)),
                "action_distribution": dict(dist),
            },
        },
        out_path,
    )

    print(f"Saved checkpoint: {out_path}")
    print(f"Metrics: {metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
