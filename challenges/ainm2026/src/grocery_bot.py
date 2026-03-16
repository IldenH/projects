#!/usr/bin/env python3
"""Expert-level Grocery Bot solver.

Usage:
  python3 grocery_bot.py "wss://game-dev.ainm.no/ws?token=..."
  WS_URL="wss://..." python3 grocery_bot.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter, deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

import websockets

Coord = Tuple[int, int]

MOVE_DELTAS = [
    ("move_up", 0, -1),
    ("move_down", 0, 1),
    ("move_left", -1, 0),
    ("move_right", 1, 0),
]


@dataclass
class Context:
    state: dict
    width: int
    height: int
    wall_set: Set[Coord]
    item_by_id: Dict[str, dict]
    items_by_type: Dict[str, List[dict]]
    active_need: Counter
    preview_need: Counter
    drop_off: Coord
    bots: List[dict]


def count_items(items: Iterable[str]) -> Counter:
    return Counter(items or [])


def subtract_counts(base: Counter, subtract: Counter) -> Counter:
    out = Counter(base)
    out.subtract(subtract)
    for k in list(out.keys()):
        if out[k] <= 0:
            del out[k]
    return out


def is_adjacent(a: Coord, b: Coord) -> bool:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


class GroceryPlanner:
    def __init__(self) -> None:
        self.shelf_set: Set[Coord] = set()
        self.round = -1
        self.game_id: Optional[str] = None

    def reset_for_new_game(self, state: dict) -> None:
        self.shelf_set.clear()
        self.round = -1
        w = state["grid"]["width"]
        h = state["grid"]["height"]
        dx, dy = state["drop_off"]
        self.game_id = f"{w}x{h}:{dx},{dy}"

    def update_shelves(self, items: List[dict]) -> None:
        for item in items:
            x, y = item["position"]
            self.shelf_set.add((x, y))

    def build_context(self, state: dict) -> Context:
        width = state["grid"]["width"]
        height = state["grid"]["height"]
        wall_set = {(x, y) for x, y in state["grid"]["walls"]}

        item_by_id = {}
        items_by_type: Dict[str, List[dict]] = {}
        for item in state["items"]:
            item_by_id[item["id"]] = item
            items_by_type.setdefault(item["type"], []).append(item)

        orders = state.get("orders", [])
        active_order = next(
            (o for o in orders if o.get("status") == "active" and not o.get("complete", False)),
            None,
        )
        preview_order = next(
            (o for o in orders if o.get("status") == "preview" and not o.get("complete", False)),
            None,
        )

        active_need = (
            subtract_counts(
                count_items(active_order.get("items_required", [])),
                count_items(active_order.get("items_delivered", [])),
            )
            if active_order
            else Counter()
        )
        preview_need = (
            subtract_counts(
                count_items(preview_order.get("items_required", [])),
                count_items(preview_order.get("items_delivered", [])),
            )
            if preview_order
            else Counter()
        )

        bots = sorted(state["bots"], key=lambda b: b["id"])
        return Context(
            state=state,
            width=width,
            height=height,
            wall_set=wall_set,
            item_by_id=item_by_id,
            items_by_type=items_by_type,
            active_need=active_need,
            preview_need=preview_need,
            drop_off=tuple(state["drop_off"]),
            bots=bots,
        )

    def is_walkable(self, ctx: Context, x: int, y: int) -> bool:
        if x < 0 or y < 0 or x >= ctx.width or y >= ctx.height:
            return False
        pos = (x, y)
        if pos in ctx.wall_set:
            return False
        if pos in self.shelf_set:
            return False
        return True

    def walkable_neighbors(self, ctx: Context, x: int, y: int) -> List[Coord]:
        out = []
        for _, dx, dy in MOVE_DELTAS:
            nx, ny = x + dx, y + dy
            if self.is_walkable(ctx, nx, ny):
                out.append((nx, ny))
        return out

    def bfs_distance_map(self, ctx: Context, start: Coord) -> Dict[Coord, int]:
        dist = {start: 0}
        q = deque([start])
        while q:
            x, y = q.popleft()
            base = dist[(x, y)]
            for nx, ny in self.walkable_neighbors(ctx, x, y):
                if (nx, ny) not in dist:
                    dist[(nx, ny)] = base + 1
                    q.append((nx, ny))
        return dist

    def pickup_cells_for_item(self, ctx: Context, item: dict) -> List[Coord]:
        ix, iy = item["position"]
        cells = []
        for _, dx, dy in MOVE_DELTAS:
            x, y = ix + dx, iy + dy
            if self.is_walkable(ctx, x, y):
                cells.append((x, y))
        return cells

    def build_bot_info(self, ctx: Context) -> List[dict]:
        infos = []
        for bot in ctx.bots:
            inv_counts = Counter(bot.get("inventory", []))
            infos.append(
                {
                    "bot": bot,
                    "inv_counts": inv_counts,
                    "dist_map": self.bfs_distance_map(ctx, tuple(bot["position"])),
                }
            )
        return infos

    def count_carry_for_need(self, bot_infos: List[dict], need_map: Counter) -> Counter:
        out = Counter()
        for info in bot_infos:
            for t, n in info["inv_counts"].items():
                if t in need_map:
                    out[t] += n
        return out

    def assign_pickups(
        self,
        ctx: Context,
        bot_infos: List[dict],
        bot_tasks: Dict[int, dict],
        need_map: Counter,
        stage: str,
        reserved_items: Set[str],
    ) -> None:
        carrying = self.count_carry_for_need(bot_infos, need_map)
        deficit = subtract_counts(need_map, carrying)

        while deficit:
            best = None
            best_item = None

            for info in bot_infos:
                bot = info["bot"]
                bot_id = bot["id"]
                if bot_id in bot_tasks:
                    continue
                if len(bot.get("inventory", [])) >= 3:
                    continue

                for item_type, needed in deficit.items():
                    if needed <= 0:
                        continue
                    for item in ctx.items_by_type.get(item_type, []):
                        if item["id"] in reserved_items:
                            continue
                        pickup_cells = self.pickup_cells_for_item(ctx, item)
                        if not pickup_cells:
                            continue

                        best_dist = min(
                            (info["dist_map"].get(cell, float("inf")) for cell in pickup_cells),
                            default=float("inf"),
                        )
                        if best_dist == float("inf"):
                            continue

                        score = best_dist + (2 if stage == "preview" else 0)
                        cand = (score, bot_id, item_type, item["id"])
                        if best is None or cand < best:
                            best = cand
                            best_item = item

            if best is None:
                break

            _, bot_id, item_type, _ = best
            item = best_item
            bot_tasks[bot_id] = {"kind": "pickup", "item_id": item["id"], "stage": stage}
            reserved_items.add(item["id"])
            deficit[item_type] -= 1
            if deficit[item_type] <= 0:
                del deficit[item_type]

    def plan_tasks(self, ctx: Context) -> Dict[int, dict]:
        bot_infos = self.build_bot_info(ctx)
        bot_tasks: Dict[int, dict] = {}
        reserved_items: Set[str] = set()

        for info in bot_infos:
            bot = info["bot"]
            inv = bot.get("inventory", [])
            has_active = any(t in ctx.active_need for t in inv)
            if has_active:
                bot_tasks[bot["id"]] = {"kind": "dropoff"}

        self.assign_pickups(ctx, bot_infos, bot_tasks, ctx.active_need, "active", reserved_items)
        self.assign_pickups(ctx, bot_infos, bot_tasks, ctx.preview_need, "preview", reserved_items)

        for info in bot_infos:
            bot = info["bot"]
            bot_id = bot["id"]
            if bot_id in bot_tasks:
                continue
            if bot.get("inventory"):
                bot_tasks[bot_id] = {"kind": "dropoff"}
            else:
                bot_tasks[bot_id] = {"kind": "wait"}

        return bot_tasks

    def next_move_toward(
        self,
        ctx: Context,
        start: Coord,
        targets: List[Coord],
        occupied_set: Set[Coord],
    ) -> Optional[Tuple[str, Coord]]:
        target_set = set(targets)
        if start in target_set:
            return None

        q = deque([start])
        seen = {start}
        prev: Dict[Coord, Coord] = {}
        found = None

        while q and found is None:
            x, y = q.popleft()
            for _, dx, dy in MOVE_DELTAS:
                nx, ny = x + dx, y + dy
                nxt = (nx, ny)
                if nxt in seen:
                    continue
                if not self.is_walkable(ctx, nx, ny):
                    continue
                if nxt in occupied_set and nxt != start:
                    continue

                seen.add(nxt)
                prev[nxt] = (x, y)
                if nxt in target_set:
                    found = nxt
                    break
                q.append(nxt)

        if found is None:
            return None

        step = found
        while True:
            p = prev.get(step)
            if p is None:
                return None
            if p == start:
                break
            step = p

        dx = step[0] - start[0]
        dy = step[1] - start[1]
        action = next((a for a, mx, my in MOVE_DELTAS if mx == dx and my == dy), None)
        if action is None:
            return None
        return action, step

    def action_for_task(self, ctx: Context, bot: dict, task: dict, occupied_set: Set[Coord]) -> dict:
        bx, by = bot["position"]
        pos = (bx, by)

        if task["kind"] == "wait":
            return {"bot": bot["id"], "action": "wait"}

        if task["kind"] == "dropoff":
            if pos == ctx.drop_off:
                active_types = set(ctx.active_need.keys())
                should_drop = any(t in active_types for t in bot.get("inventory", []))
                return {"bot": bot["id"], "action": "drop_off" if should_drop else "wait"}

            mv = self.next_move_toward(ctx, pos, [ctx.drop_off], occupied_set)
            if mv is None:
                return {"bot": bot["id"], "action": "wait"}
            action, to = mv
            return {"bot": bot["id"], "action": action, "_to": to}

        if task["kind"] == "pickup":
            item = ctx.item_by_id.get(task["item_id"])
            if item is None:
                return {"bot": bot["id"], "action": "wait"}
            if len(bot.get("inventory", [])) >= 3:
                return {"bot": bot["id"], "action": "wait"}

            item_pos = tuple(item["position"])
            if is_adjacent(pos, item_pos):
                return {"bot": bot["id"], "action": "pick_up", "item_id": item["id"]}

            targets = self.pickup_cells_for_item(ctx, item)
            if not targets:
                return {"bot": bot["id"], "action": "wait"}

            mv = self.next_move_toward(ctx, pos, targets, occupied_set)
            if mv is None:
                return {"bot": bot["id"], "action": "wait"}
            action, to = mv
            return {"bot": bot["id"], "action": action, "_to": to}

        return {"bot": bot["id"], "action": "wait"}

    def decide_actions(self, state: dict) -> List[dict]:
        new_game = state.get("round", 0) == 0 or self.round > state.get("round", 0)
        if new_game or self.game_id is None:
            self.reset_for_new_game(state)
        self.round = state.get("round", 0)

        self.update_shelves(state.get("items", []))
        ctx = self.build_context(state)
        tasks = self.plan_tasks(ctx)

        occupied = {tuple(b["position"]) for b in ctx.bots}
        actions = []

        for bot in ctx.bots:
            pos = tuple(bot["position"])
            task = tasks.get(bot["id"], {"kind": "wait"})
            action = self.action_for_task(ctx, bot, task, occupied)

            if "_to" in action:
                to = action["_to"]
                if to not in occupied:
                    occupied.discard(pos)
                    occupied.add(to)
                else:
                    action["action"] = "wait"
                del action["_to"]

            actions.append(action)

        return actions


async def run(ws_url: str) -> None:
    planner = GroceryPlanner()

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

            actions = planner.decide_actions(msg)
            await ws.send(json.dumps({"actions": actions}))


def main() -> int:
    ws_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("WS_URL")
    if not ws_url:
        print('Usage: python3 grocery_bot.py "wss://game-dev.ainm.no/ws?token=..."')
        print('   or: WS_URL="wss://..." python3 grocery_bot.py')
        return 1

    try:
        asyncio.run(run(ws_url))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
