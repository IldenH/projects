#!/usr/bin/env python3
"""DAgger-style replay collector for Grocery Bot.

Collects trajectories from live games while logging expert labels.
Supports round-level expert/student mixing and quality gates so only
high-quality runs are saved.

Examples:
  python3 collect_dagger.py --ws-url "wss://game-dev.ainm.no/ws?token=..."
  python3 collect_dagger.py --ws-urls-file ws_urls.txt --mode mix --games 4
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import os
import random
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import websockets

from grocery_bot import GroceryPlanner
from tianshou_bot import PolicyConfig, TianshouActionPolicy, TianshouGroceryBot


def now_ts() -> int:
    return int(time.time())


def parse_ws_urls(args) -> List[str]:
    urls: List[str] = []
    if args.ws_url:
        urls.extend(args.ws_url)
    if args.ws_urls_file:
        with open(args.ws_urls_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    if not urls:
        env_url = os.getenv("WS_URL")
        if env_url:
            urls.append(env_url)
    if not urls:
        raise RuntimeError("No WebSocket URLs provided. Use --ws-url, --ws-urls-file, or WS_URL.")
    return urls


def pick_behavior(mode: str, beta: float) -> str:
    if mode == "expert":
        return "expert"
    if mode == "student":
        return "student"
    return "expert" if random.random() < beta else "student"


def beta_for_game(game_idx: int, total_games: int, beta_start: float, beta_end: float) -> float:
    if total_games <= 1:
        return beta_end
    t = game_idx / max(total_games - 1, 1)
    return beta_start + (beta_end - beta_start) * t


def action_hist(actions: List[dict]) -> Counter:
    c = Counter()
    for a in actions:
        c[a.get("action", "wait")] += 1
    return c


def summarize_traj(trajectory: List[dict]) -> Dict[str, int]:
    executed = Counter()
    expert = Counter()
    student = Counter()
    for step in trajectory:
        executed.update(action_hist(step.get("actions", [])))
        expert.update(action_hist(step.get("expert_actions", [])))
        student.update(action_hist(step.get("student_actions", [])))
    out = {}
    for k, v in executed.items():
        out[f"exec_{k}"] = int(v)
    for k, v in expert.items():
        out[f"expert_{k}"] = int(v)
    for k, v in student.items():
        out[f"student_{k}"] = int(v)
    return out


async def collect_one_game(
    ws_url: str,
    mode: str,
    beta: float,
    student_bot: TianshouGroceryBot,
    expert_planner: GroceryPlanner,
) -> dict:
    trajectory: List[dict] = []
    source_counts = Counter()
    prev_score = None

    async with websockets.connect(ws_url, max_size=4_000_000) as ws:
        async for raw in ws:
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "game_over":
                return {
                    "trajectory": trajectory,
                    "game_over": msg,
                    "source_counts": dict(source_counts),
                }

            if msg_type != "game_state":
                continue

            if msg.get("round", 0) == 0:
                expert_planner.reset_for_new_game(msg)

            expert_actions = expert_planner.decide_actions(msg)
            student_actions = student_bot.decide_actions(msg)

            source = pick_behavior(mode=mode, beta=beta)
            source_counts[source] += 1
            send_actions = expert_actions if source == "expert" else student_actions

            curr_score = msg.get("score", 0)
            reward = 0.0 if prev_score is None else float(curr_score - prev_score)
            prev_score = curr_score

            trajectory.append(
                {
                    "round": msg.get("round", 0),
                    "state": msg,
                    "actions": send_actions,
                    "expert_actions": expert_actions,
                    "student_actions": student_actions,
                    "action_source": source,
                    "beta": beta,
                    "reward": reward,
                }
            )

            await ws.send(json.dumps({"actions": send_actions}))

    raise RuntimeError("Connection closed before game_over")


def passes_quality(result: dict, min_score: int, min_pickups: int, min_dropoffs: int) -> bool:
    go = result.get("game_over", {})
    if go.get("score", 0) < min_score:
        return False

    counts = summarize_traj(result.get("trajectory", []))
    exec_pickups = counts.get("exec_pick_up", 0)
    exec_dropoffs = counts.get("exec_drop_off", 0)

    if exec_pickups < min_pickups:
        return False
    if exec_dropoffs < min_dropoffs:
        return False
    return True


def save_game(out_dir: Path, game_idx: int, ws_url: str, beta: float, mode: str, result: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    dims = None
    if result.get("trajectory"):
        s0 = result["trajectory"][0]["state"]
        dims = f"{s0['grid']['width']}x{s0['grid']['height']}"
    suffix = dims or "unknown"

    path = out_dir / f"dagger_{now_ts()}_{game_idx}_{suffix}.json.gz"
    payload = {
        "game_idx": game_idx,
        "mode": mode,
        "beta": beta,
        "ws_url_redacted": ws_url.split("?", 1)[0],
        "trajectory": result.get("trajectory", []),
        "game_over": result.get("game_over", {}),
        "source_counts": result.get("source_counts", {}),
        "action_summary": summarize_traj(result.get("trajectory", [])),
    }
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    return path


async def main_async(args) -> int:
    random.seed(args.seed)

    urls = parse_ws_urls(args)
    total_games = args.games or len(urls)

    policy = TianshouActionPolicy(
        PolicyConfig(device=args.device, checkpoint=args.student_checkpoint)
    )
    if policy.import_error is not None:
        print(f"Tianshou unavailable ({policy.import_error}); student policy will fall back.")
    if args.student_checkpoint and not policy.ready:
        print("Warning: student checkpoint not loaded; student actions will be heuristic fallback.")

    student_bot = TianshouGroceryBot(policy)
    out_dir = Path(args.out_dir)

    saved = 0
    skipped = 0

    for i in range(total_games):
        ws_url = urls[i % len(urls)]
        expert = GroceryPlanner()
        beta = beta_for_game(i, total_games, args.beta_start, args.beta_end)

        print(f"game {i+1}/{total_games}: mode={args.mode} beta={beta:.3f}")
        result = await collect_one_game(
            ws_url=ws_url,
            mode=args.mode,
            beta=beta,
            student_bot=student_bot,
            expert_planner=expert,
        )

        go = result.get("game_over", {})
        counts = summarize_traj(result.get("trajectory", []))
        print(
            f"  score={go.get('score')} orders={go.get('orders_completed')} "
            f"pickups={counts.get('exec_pick_up',0)} dropoffs={counts.get('exec_drop_off',0)}"
        )

        if passes_quality(
            result,
            min_score=args.min_score,
            min_pickups=args.min_pickups,
            min_dropoffs=args.min_dropoffs,
        ):
            path = save_game(out_dir, i, ws_url, beta, args.mode, result)
            print(f"  saved: {path}")
            saved += 1
        else:
            print("  skipped: did not pass quality thresholds")
            skipped += 1

        if i + 1 < total_games and args.cooldown_sec > 0:
            await asyncio.sleep(args.cooldown_sec)

    print(f"done: saved={saved} skipped={skipped} out_dir={out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--ws-url", action="append", help="WebSocket URL (repeatable)")
    p.add_argument("--ws-urls-file", help="Path to newline-delimited WS URLs")
    p.add_argument("--games", type=int, default=0, help="Number of games to collect (default=len(urls))")

    p.add_argument("--mode", choices=["expert", "student", "mix"], default="mix")
    p.add_argument("--beta-start", type=float, default=0.8, help="Expert probability at first game in mix mode")
    p.add_argument("--beta-end", type=float, default=0.2, help="Expert probability at last game in mix mode")

    p.add_argument("--student-checkpoint", default=os.getenv("TS_CHECKPOINT"))
    p.add_argument("--device", default=os.getenv("TS_DEVICE", "cpu"))

    p.add_argument("--min-score", type=int, default=20)
    p.add_argument("--min-pickups", type=int, default=4)
    p.add_argument("--min-dropoffs", type=int, default=2)
    p.add_argument("--cooldown-sec", type=float, default=10.5)

    p.add_argument("--out-dir", default="replays_dagger")
    p.add_argument("--seed", type=int, default=7)
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
