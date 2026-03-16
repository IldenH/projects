#!/usr/bin/env python3
"""Grocery bot with Tianshou-driven action selection.

This keeps the expert heuristic planner for task assignment/pathing and lets a
Tianshou Q-network choose primitive actions per bot when a checkpoint is loaded.
Without a checkpoint, it falls back to heuristic actions.

Usage:
  python3 tianshou_bot.py "wss://game-dev.ainm.no/ws?token=..."
  WS_URL="wss://..." python3 tianshou_bot.py

Optional env vars:
  TS_CHECKPOINT=/path/to/model.pt
  TS_DEVICE=cpu|cuda
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import torch
import websockets

from grocery_bot import GroceryPlanner, MOVE_DELTAS

try:
    from tianshou.utils.net.common import Net
except Exception as exc:  # pragma: no cover
    Net = None
    _TS_IMPORT_ERROR = exc
else:
    _TS_IMPORT_ERROR = None

Coord = Tuple[int, int]

ACTION_TO_ID = {
    "wait": 0,
    "move_up": 1,
    "move_down": 2,
    "move_left": 3,
    "move_right": 4,
    "pick_up": 5,
    "drop_off": 6,
}
ID_TO_ACTION = {v: k for k, v in ACTION_TO_ID.items()}


@dataclass
class PolicyConfig:
    obs_dim: int = 24
    action_dim: int = 7
    hidden_sizes: Tuple[int, int] = (128, 128)
    device: str = "cpu"
    checkpoint: Optional[str] = None


class TianshouActionPolicy:
    def __init__(self, cfg: PolicyConfig) -> None:
        self.cfg = cfg
        self.device = torch.device(cfg.device)
        self.ready = False
        self.net = None
        self.import_error = _TS_IMPORT_ERROR

        if Net is None:
            return

        self.net = Net(
            state_shape=(cfg.obs_dim,),
            action_shape=cfg.action_dim,
            hidden_sizes=list(cfg.hidden_sizes),
            device=str(self.device),
        ).to(self.device)
        self.net.eval()

        if cfg.checkpoint and os.path.exists(cfg.checkpoint):
            blob = torch.load(cfg.checkpoint, map_location=self.device)
            if isinstance(blob, dict) and "model" in blob:
                self.net.load_state_dict(blob["model"])
            elif isinstance(blob, dict):
                self.net.load_state_dict(blob)
            else:
                raise RuntimeError("Unsupported checkpoint format for TS_CHECKPOINT")
            self.ready = True

    def choose(self, obs: np.ndarray, mask: np.ndarray) -> int:
        if not self.ready or self.net is None:
            return ACTION_TO_ID["wait"]

        with torch.no_grad():
            x = torch.as_tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)
            logits, _ = self.net(x)
            q = logits.squeeze(0).detach().cpu().numpy()

        q = np.where(mask > 0, q, -1e9)
        return int(np.argmax(q))


class TianshouGroceryBot:
    def __init__(self, policy: TianshouActionPolicy) -> None:
        self.policy = policy
        self.planner = GroceryPlanner()

    def _build_context(self, state: dict):
        self.planner.update_shelves(state.get("items", []))
        return self.planner.build_context(state)

    def _adjacent_pickable_item_id(self, bot: dict, ctx, preferred: Optional[str]) -> Optional[str]:
        if preferred:
            item = ctx.item_by_id.get(preferred)
            if item:
                bx, by = bot["position"]
                ix, iy = item["position"]
                if abs(bx - ix) + abs(by - iy) == 1:
                    return preferred

        active_types = set(ctx.active_need.keys())
        preview_types = set(ctx.preview_need.keys())

        bx, by = bot["position"]
        for item in ctx.state["items"]:
            ix, iy = item["position"]
            if abs(bx - ix) + abs(by - iy) != 1:
                continue
            if item["type"] in active_types:
                return item["id"]
        for item in ctx.state["items"]:
            ix, iy = item["position"]
            if abs(bx - ix) + abs(by - iy) != 1:
                continue
            if item["type"] in preview_types:
                return item["id"]
        return None

    def _valid_mask(self, bot: dict, ctx, occupied: Set[Coord]) -> np.ndarray:
        mask = np.zeros(7, dtype=np.float32)
        bx, by = bot["position"]

        mask[ACTION_TO_ID["wait"]] = 1.0

        for action, dx, dy in MOVE_DELTAS:
            nx, ny = bx + dx, by + dy
            if self.planner.is_walkable(ctx, nx, ny) and (nx, ny) not in occupied:
                mask[ACTION_TO_ID[action]] = 1.0

        if len(bot.get("inventory", [])) < 3:
            if self._adjacent_pickable_item_id(bot, ctx, None) is not None:
                mask[ACTION_TO_ID["pick_up"]] = 1.0

        if tuple(bot["position"]) == tuple(ctx.drop_off) and len(bot.get("inventory", [])) > 0:
            mask[ACTION_TO_ID["drop_off"]] = 1.0

        return mask

    def _obs(self, state: dict, bot: dict, ctx, heuristic_action: str) -> np.ndarray:
        w = max(1, state["grid"]["width"] - 1)
        h = max(1, state["grid"]["height"] - 1)

        bx, by = bot["position"]
        dx, dy = ctx.drop_off

        inv = bot.get("inventory", [])
        inv_len = len(inv)

        active_need_total = float(sum(ctx.active_need.values()))
        preview_need_total = float(sum(ctx.preview_need.values()))

        inv_active = sum(1 for t in inv if t in ctx.active_need)
        inv_preview = sum(1 for t in inv if t in ctx.preview_need)

        nearest_active = 1.0
        nearest_preview = 1.0
        if ctx.state["items"]:
            active_types = set(ctx.active_need.keys())
            preview_types = set(ctx.preview_need.keys())
            active_dists = []
            preview_dists = []
            for it in ctx.state["items"]:
                ix, iy = it["position"]
                d = abs(bx - ix) + abs(by - iy)
                if it["type"] in active_types:
                    active_dists.append(d)
                if it["type"] in preview_types:
                    preview_dists.append(d)
            if active_dists:
                nearest_active = min(active_dists) / (w + h)
            if preview_dists:
                nearest_preview = min(preview_dists) / (w + h)

        heur_onehot = np.zeros(7, dtype=np.float32)
        heur_onehot[ACTION_TO_ID.get(heuristic_action, 0)] = 1.0

        vec = np.array(
            [
                bx / w,
                by / h,
                dx / w,
                dy / h,
                abs(bx - dx) / (w + h),
                abs(by - dy) / (w + h),
                inv_len / 3.0,
                min(inv_active / 3.0, 1.0),
                min(inv_preview / 3.0, 1.0),
                min(active_need_total / 8.0, 1.0),
                min(preview_need_total / 8.0, 1.0),
                nearest_active,
                nearest_preview,
                state.get("round", 0) / max(1, state.get("max_rounds", 300)),
                float(len(state.get("bots", []))) / 10.0,
                float(len(state.get("items", []))) / 128.0,
                float(mask_count_walkable_moves(bot, ctx, self.planner)) / 4.0,
            ],
            dtype=np.float32,
        )

        out = np.concatenate([vec, heur_onehot], axis=0)
        if out.shape[0] != 24:
            raise RuntimeError(f"Unexpected obs size: {out.shape[0]}")
        return out

    def decide_actions(self, state: dict) -> List[dict]:
        heuristic_actions = self.planner.decide_actions(state)
        by_id = {a["bot"]: a for a in heuristic_actions}

        if not self.policy.ready:
            return heuristic_actions

        ctx = self._build_context(state)
        bots = sorted(state["bots"], key=lambda b: b["id"])

        occupied = {tuple(b["position"]) for b in bots}
        actions: List[dict] = []

        for bot in bots:
            bot_id = bot["id"]
            heuristic = by_id.get(bot_id, {"bot": bot_id, "action": "wait"})
            heur_name = heuristic["action"]

            from_pos = tuple(bot["position"])
            occupied.discard(from_pos)
            mask = self._valid_mask(bot, ctx, occupied)
            obs = self._obs(state, bot, ctx, heur_name)
            act_id = self.policy.choose(obs, mask)
            act_name = ID_TO_ACTION.get(act_id, "wait")

            selected = {"bot": bot_id, "action": act_name}

            if mask[act_id] <= 0:
                selected = heuristic
            elif act_name == "pick_up":
                item_id = self._adjacent_pickable_item_id(bot, ctx, heuristic.get("item_id"))
                if item_id is None:
                    selected = heuristic
                else:
                    selected["item_id"] = item_id
            elif act_name.startswith("move_"):
                dx, dy = action_delta(act_name)
                to = (from_pos[0] + dx, from_pos[1] + dy)
                if to in occupied or not self.planner.is_walkable(ctx, to[0], to[1]):
                    selected = heuristic
                else:
                    occupied.add(to)
            elif act_name == "drop_off":
                if tuple(bot["position"]) != tuple(state["drop_off"]):
                    selected = heuristic
            else:
                occupied.add(from_pos)

            # Maintain conservative collision handling if heuristic move chosen as fallback.
            if selected["action"].startswith("move_"):
                dx, dy = action_delta(selected["action"])
                to = (from_pos[0] + dx, from_pos[1] + dy)
                if to in occupied or not self.planner.is_walkable(ctx, to[0], to[1]):
                    selected = {"bot": bot_id, "action": "wait"}
                    occupied.add(from_pos)
                else:
                    occupied.add(to)
            elif selected["action"] in ("wait", "pick_up", "drop_off"):
                occupied.add(from_pos)

            actions.append(selected)

        return actions


def mask_count_walkable_moves(bot: dict, ctx, planner: GroceryPlanner) -> int:
    x, y = bot["position"]
    c = 0
    for _, dx, dy in MOVE_DELTAS:
        if planner.is_walkable(ctx, x + dx, y + dy):
            c += 1
    return c


def action_delta(action: str) -> Tuple[int, int]:
    for name, dx, dy in MOVE_DELTAS:
        if action == name:
            return dx, dy
    return 0, 0


async def run(ws_url: str, bot: TianshouGroceryBot) -> None:
    async with websockets.connect(ws_url, max_size=4_000_000) as ws:
        print("Connected to game server.")

        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            if msg_type == "game_over":
                print(
                    f"Game over: score={msg.get('score')}, rounds={msg.get('rounds_used')}, "
                    f"items={msg.get('items_delivered')}, orders={msg.get('orders_completed')}"
                )
                return

            if msg_type != "game_state":
                continue

            actions = bot.decide_actions(msg)
            await ws.send(json.dumps({"actions": actions}))


def main() -> int:
    ws_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("WS_URL")
    if not ws_url:
        print('Usage: python3 tianshou_bot.py "wss://game-dev.ainm.no/ws?token=..."')
        print('   or: WS_URL="wss://..." python3 tianshou_bot.py')
        return 1

    device = os.getenv("TS_DEVICE", "cpu")
    ckpt = os.getenv("TS_CHECKPOINT")

    policy = TianshouActionPolicy(PolicyConfig(device=device, checkpoint=ckpt))

    if policy.ready:
        print(f"Tianshou checkpoint loaded: {ckpt}")
    elif policy.import_error is not None:
        print(f"Tianshou unavailable ({policy.import_error}); running heuristic fallback.")
    else:
        print("No TS_CHECKPOINT loaded; using heuristic actions while keeping Tianshou wiring in place.")

    bot = TianshouGroceryBot(policy)

    try:
        asyncio.run(run(ws_url, bot))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
