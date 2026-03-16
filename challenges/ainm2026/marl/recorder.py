"""
recorder.py — Connect to the grocery game server and save full episode replays.

Usage:
    python recorder.py --token YOUR_TOKEN --out replays/ --games 5 --difficulty easy

The recorder plays using the greedy baseline bot and saves every (state, actions, reward)
transition to a compressed JSON file.  These recordings feed the offline simulator.
"""

import asyncio
import json
import os
import time
import argparse
import gzip
from pathlib import Path
from typing import Any

WS_URL = "wss://game.ainm.no/ws?token={token}"


# ---------------------------------------------------------------------------
# Greedy baseline (same logic as the example bot — used to generate replays)
# ---------------------------------------------------------------------------

def greedy_decide(bot: dict, state: dict, claimed: set[str]) -> dict:
    """Simple greedy policy used to generate training rollouts."""
    x, y = bot["position"]
    drop_off = state["drop_off"]
    bot_id = bot["id"]

    # Drop off if on the zone and carrying anything
    if bot["inventory"] and [x, y] == drop_off:
        return {"bot": bot_id, "action": "drop_off"}

    # Head to drop-off if inventory full
    if len(bot["inventory"]) >= 3:
        return _move_toward(bot_id, x, y, drop_off)

    active = next((o for o in state["orders"] if o["status"] == "active"), None)
    preview = next((o for o in state["orders"] if o["status"] == "preview"), None)

    needed = _needed_items(active) if active else []
    # Also consider picking preview items if active is nearly done
    preview_needed = _needed_items(preview) if preview else []
    all_needed = needed + [p for p in preview_needed if p not in needed]

    # Try to pick up an adjacent needed item not already claimed
    for item in state["items"]:
        if item["type"] in all_needed and item["id"] not in claimed:
            ix, iy = item["position"]
            if abs(ix - x) + abs(iy - y) == 1:
                claimed.add(item["id"])
                return {"bot": bot_id, "action": "pick_up", "item_id": item["id"]}

    # Move toward nearest unclaimed needed item
    best = None
    best_dist = 999
    for item in state["items"]:
        if item["type"] in all_needed and item["id"] not in claimed:
            ix, iy = item["position"]
            d = abs(ix - x) + abs(iy - y)
            if d < best_dist:
                best_dist = d
                best = item

    if best:
        claimed.add(best["id"])
        return _move_toward(bot_id, x, y, best["position"])

    if bot["inventory"]:
        return _move_toward(bot_id, x, y, drop_off)

    return {"bot": bot_id, "action": "wait"}


def _needed_items(order: dict | None) -> list[str]:
    if not order:
        return []
    needed = list(order["items_required"])
    for d in order["items_delivered"]:
        if d in needed:
            needed.remove(d)
    # Also subtract what's already in inventories (caller handles this)
    return needed


def _move_toward(bot_id: int, x: int, y: int, target: list[int]) -> dict:
    tx, ty = target
    if abs(tx - x) > abs(ty - y):
        return {"bot": bot_id, "action": "move_right" if tx > x else "move_left"}
    elif ty != y:
        return {"bot": bot_id, "action": "move_down" if ty > y else "move_up"}
    return {"bot": bot_id, "action": "wait"}


# ---------------------------------------------------------------------------
# Reward shaping (mirrors the RL reward function)
# ---------------------------------------------------------------------------

def compute_reward(prev_state: dict | None, curr_state: dict) -> float:
    """Dense reward signal computed from two consecutive states."""
    if prev_state is None:
        return 0.0

    reward = 0.0

    # Score delta (includes +1 per item delivered and +5 per order)
    score_delta = curr_state["score"] - prev_state["score"]
    reward += score_delta * 1.0

    # Small bonus for each item picked up across all bots
    prev_inv = sum(len(b["inventory"]) for b in prev_state["bots"])
    curr_inv = sum(len(b["inventory"]) for b in curr_state["bots"])
    items_picked = max(0, curr_inv - prev_inv)
    reward += items_picked * 0.2

    # Penalty per idle bot (encourages activity)
    idle = sum(1 for b in curr_state["bots"] if not b["inventory"])
    reward -= idle * 0.05

    return round(reward, 4)


# ---------------------------------------------------------------------------
# Recorder
# ---------------------------------------------------------------------------

async def record_game(token: str, out_dir: Path, game_idx: int) -> dict:
    """Play one game with the greedy bot and save the full trajectory."""
    import websockets  # lazy import — only needed when recording

    url = WS_URL.format(token=token)
    trajectory: list[dict] = []
    prev_state: dict | None = None

    print(f"[{game_idx}] Connecting...")
    async with websockets.connect(url, ping_interval=20) as ws:
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)

            if msg["type"] == "game_over":
                print(f"[{game_idx}] Game over — score: {msg['score']}")
                break

            state = msg
            claimed: set[str] = set()
            actions = []

            for bot in state["bots"]:
                action = greedy_decide(bot, state, claimed)
                actions.append(action)

            reward = compute_reward(prev_state, state)

            trajectory.append({
                "round": state["round"],
                "state": state,
                "actions": actions,
                "reward": reward,
            })

            prev_state = state
            await ws.send(json.dumps({"actions": actions}))

    # Save compressed replay
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / f"replay_{int(time.time())}_{game_idx}.json.gz"
    with gzip.open(fname, "wt", encoding="utf-8") as f:
        json.dump({"trajectory": trajectory, "game_idx": game_idx}, f)

    print(f"[{game_idx}] Saved → {fname}  ({len(trajectory)} rounds)")
    return {"file": str(fname), "rounds": len(trajectory)}


async def main(args):
    out_dir = Path(args.out)
    results = []
    for i in range(args.games):
        try:
            r = await record_game(args.token, out_dir, i)
            results.append(r)
        except Exception as e:
            print(f"[{i}] Error: {e}")
        if i < args.games - 1:
            print(f"Cooldown 65s...")
            await asyncio.sleep(65)

    summary = out_dir / "recordings_index.json"
    with open(summary, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. {len(results)} replays saved to {out_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record grocery-bot game replays.")
    parser.add_argument("--token", required=True, help="JWT token from app.ainm.no")
    parser.add_argument("--out", default="replays", help="Output directory")
    parser.add_argument("--games", type=int, default=3, help="Number of games to record")
    args = parser.parse_args()
    asyncio.run(main(args))
