"""
Grocery Bot — Expert-grade multi-bot coordinator.

Features:
  - Windowed cooperative pathfinding (collision handling)
  - Workload balancing (reassign idle bots, cap per-bot load)
  - Swarm zoning (partition map sections by bot id)
  - Preview prefetching (fill spare slots with next-order items)
  - Zero idle time (every bot has a task every round)
"""
import asyncio
import heapq
import json
import os
import websockets
from itertools import permutations

WS_URL = os.environ.get("WS_URL", "wss://game-dev.ainm.no/ws?token=YOUR_TOKEN_HERE")


# ===========================================================================
# BFS — deterministic (heapq x,y tiebreak)
# ===========================================================================

def bfs(start, goal, wall_set, width, height, mode='to'):
    """
    mode='to'  → walk onto goal cell
    mode='adj' → reach any cell adjacent to goal (item pickup)
    Returns action list | [] if already there | None if unreachable.
    """
    sx, sy = int(start[0]), int(start[1])
    gx, gy = int(goal[0]),  int(goal[1])

    def ok(x, y):
        return (x,y)==(gx,gy) if mode=='to' else abs(x-gx)+abs(y-gy)==1

    if ok(sx, sy): return []
    heap    = [(0, sx, sy, [])]
    visited = {(sx, sy)}
    DIRS    = [("move_up",0,-1),("move_down",0,1),("move_left",-1,0),("move_right",1,0)]
    while heap:
        d, cx, cy, path = heapq.heappop(heap)
        for act, dx, dy in DIRS:
            nx, ny = cx+dx, cy+dy
            if not (0<=nx<width and 0<=ny<height): continue
            if (nx,ny) in wall_set or (nx,ny) in visited: continue
            np = path + [act]
            if ok(nx, ny): return np
            visited.add((nx,ny))
            heapq.heappush(heap, (d+1, nx, ny, np))
    return None


# ===========================================================================
# Distance cache (shelves never move → cache forever)
# ===========================================================================
_dc: dict = {}

def cdist(a, b, wall_set, width, height, mode='adj'):
    key = (tuple(a), tuple(b), mode)
    if key not in _dc:
        p = bfs(a, b, wall_set, width, height, mode)
        _dc[key] = len(p) if p is not None else 999999
    return _dc[key]


# ===========================================================================
# TSP for a single inventory trip (≤3 items)
# ===========================================================================

def tsp(start, items, drop, wall_set, width, height):
    if not items: return []
    if len(items) == 1: return list(items)
    best_cost, best_order = None, None
    for perm in permutations(items):
        cost, cur = 0, tuple(start)
        for item in perm:
            cost += cdist(cur, tuple(item["position"]), wall_set, width, height, 'adj')
            cur = tuple(item["position"])
        cost += cdist(cur, tuple(drop), wall_set, width, height, 'to')
        if best_cost is None or cost < best_cost:
            best_cost, best_order = cost, list(perm)
    return best_order


# ===========================================================================
# Helpers
# ===========================================================================

def needed_for(order):
    if not order: return []
    needed = list(order["items_required"])
    for d in order["items_delivered"]:
        if d in needed: needed.remove(d)
    return needed

def match_items(types, items_on_map, exclude_ids=None):
    result, used = [], set(exclude_ids or [])
    for t in types:
        for item in items_on_map:
            if item["type"] == t and item["id"] not in used:
                result.append(item)
                used.add(item["id"])
                break
    return result

DELTAS = {"move_up":(0,-1),"move_down":(0,1),"move_left":(-1,0),"move_right":(1,0)}

def sim_pos(pos, action):
    if action not in DELTAS: return tuple(pos)
    dx, dy = DELTAS[action]
    return (pos[0]+dx, pos[1]+dy)


# ===========================================================================
# Swarm Zoning
# Divide the map into vertical bands, one per bot.
# When multiple items of the same type exist, prefer the one in the bot's zone.
# This reduces cross-traffic and spread bots across the store.
# ===========================================================================

def zone_for_bot(bot_id, n_bots, width):
    """Return (x_min, x_max) inclusive for this bot's preferred zone."""
    band = width / n_bots
    return (int(bot_id * band), int((bot_id + 1) * band) - 1)

def zone_score(item_pos, bot_id, n_bots, width):
    """Lower = more preferred. Items in bot's zone score 0, others score distance from zone."""
    x = item_pos[0]
    lo, hi = zone_for_bot(bot_id, n_bots, width)
    if lo <= x <= hi: return 0
    return min(abs(x - lo), abs(x - hi))


# ===========================================================================
# Assignment with workload balancing + zoning
# ===========================================================================

def make_assignments(bots, to_fetch, drop, wall_set, width, height):
    """
    Assign items to bots. Each item goes to the bot with the best combined score:
      score = dist_to_item + zone_penalty
    Caps each bot at 3 items (inventory limit). Balances load: prefers bots
    with fewer items already assigned.
    Returns {bot_id: [item, ...]} TSP-sorted.
    """
    n_bots  = len(bots)
    free    = {b["id"]: 3 - len(b["inventory"]) for b in bots}
    load    = {b["id"]: 0 for b in bots}   # items assigned this round
    by_id   = {b["id"]: b for b in bots}
    result  = {b["id"]: [] for b in bots}

    for item in to_fetch:
        best_id, best_score = None, 999999
        for bid, slots in free.items():
            if slots <= 0: continue
            bot = by_id[bid]
            d   = cdist(tuple(bot["position"]), tuple(item["position"]),
                        wall_set, width, height, 'adj')
            # Penalise heavily loaded bots to spread work
            balance_penalty = load[bid] * 4
            z   = zone_score(item["position"], bid, n_bots, width)
            score = d + balance_penalty + z
            if score < best_score:
                best_score, best_id = score, bid
        if best_id is not None:
            result[best_id].append(item)
            free[best_id]  -= 1
            load[best_id]  += 1

    # TSP-sort each bot's list
    for bid in result:
        if len(result[bid]) > 1:
            result[bid] = tsp(tuple(by_id[bid]["position"]), result[bid],
                              tuple(drop), wall_set, width, height)
    return result


# ===========================================================================
# Global state
# ===========================================================================
_assignments: dict = {}
_last_sig = None


def refresh(bots, state, wall_set):
    """
    Recompute assignments whenever the unmet-item set changes.
    Preview prefetching: idle bots are sent to fetch next-order items.
    Zero idle time: every bot with free slots gets something to do.
    """
    global _assignments, _last_sig

    items         = state["items"]
    drop          = state["drop_off"]
    width         = state["grid"]["width"]
    height        = state["grid"]["height"]
    active_order  = next((o for o in state["orders"] if o["status"] == "active"), None)
    preview_order = next((o for o in state["orders"] if o["status"] == "preview"), None)
    active_types  = needed_for(active_order)
    preview_types = needed_for(preview_order)
    order_id      = active_order["id"] if active_order else None
    live_ids      = {i["id"] for i in items}

    # Items the active order still needs that no bot is holding
    held = []
    for b in bots: held.extend(b["inventory"])
    unmet = list(active_types)
    for t in held:
        if t in unmet: unmet.remove(t)
    unmet_items = match_items(unmet, items)

    sig = (order_id, frozenset(i["id"] for i in unmet_items))
    if sig == _last_sig:
        # Prune picked-up items
        for bid in _assignments:
            _assignments[bid] = [i for i in _assignments[bid] if i["id"] in live_ids]
        return
    _last_sig = sig

    # Preview prefetch: fill every spare slot across all bots
    # Count how many slots are free across the swarm after assigning active items
    total_free_after = sum(max(0, 3 - len(b["inventory"])) for b in bots) - len(unmet_items)
    preview_cap = max(0, total_free_after)
    preview_items = match_items(
        preview_types[:preview_cap], items,
        exclude_ids={i["id"] for i in unmet_items}
    )

    to_fetch  = unmet_items + preview_items
    new_asgn  = make_assignments(bots, to_fetch, drop, wall_set, width, height)

    for b in bots:
        bid = b["id"]
        has_active = any(t in b["inventory"] for t in active_types)
        # Don't override a delivering bot with an empty assignment
        if has_active and not new_asgn.get(bid):
            _assignments[bid] = []
        else:
            _assignments[bid] = new_asgn.get(bid, [])

    print(f"  [COORD] order={order_id} unmet={len(unmet_items)} preview={len(preview_items)}")
    print(f"  [COORD] asgn={ {k:[(i['type'],i['position']) for i in v] for k,v in _assignments.items()} }")


# ===========================================================================
# Windowed cooperative pathfinding (collision handling)
#
# ALL bot positions start as occupied.
# Bots are decided in priority order (delivering bots first, closest to drop first).
# Each bot:
#   1. Removes its own current cell from occupied
#   2. Treats occupied as soft walls (routes around other bots)
#   3. Falls back to hard-walls-only if no path exists through soft walls
#   4. Reserves its next cell in occupied
#
# This prevents head-on swaps and chain deadlocks.
# ===========================================================================

def decide_all(bots, state, wall_set):
    items        = state["items"]
    drop         = tuple(state["drop_off"])
    width        = state["grid"]["width"]
    height       = state["grid"]["height"]
    live         = {i["id"] for i in items}
    active_order = next((o for o in state["orders"] if o["status"] == "active"), None)
    active_types = needed_for(active_order)

    occupied = {tuple(b["position"]) for b in bots}

    def priority(b):
        has_active   = any(t in b["inventory"] for t in active_types)
        d_drop       = abs(b["position"][0]-drop[0]) + abs(b["position"][1]-drop[1])
        # Delivering bots closest to drop-off go first (clear the corridor)
        return (0 if has_active else 1, d_drop, b["id"])

    action_map = {}

    for bot in sorted(bots, key=priority):
        bid = bot["id"]
        pos = tuple(bot["position"])
        inv = bot["inventory"]
        has_active = any(t in inv for t in active_types)

        occupied.discard(pos)
        soft_walls = wall_set | occupied

        assigned     = [i for i in _assignments.get(bid, []) if i["id"] in live]
        inv_copy     = list(inv)
        still_to_get = []
        for item in assigned:
            if item["type"] in inv_copy: inv_copy.remove(item["type"])
            else: still_to_get.append(item)

        action = _one(bid, pos, inv, has_active, still_to_get,
                      drop, wall_set, soft_walls, width, height)

        occupied.add(sim_pos(pos, action.get("action","wait")))
        action_map[bid] = action

    return action_map


def _one(bid, pos, inv, has_active, still_to_get, drop, wall_set, soft_walls, width, height):
    def nav(goal, mode):
        p = bfs(pos, goal, soft_walls, width, height, mode)
        if p is None:
            p = bfs(pos, goal, wall_set, width, height, mode)
        return p

    def act(path, fallback="wait"):
        if path is None:   return {"bot": bid, "action": fallback}
        if not path:       return {"bot": bid, "action": fallback}
        return {"bot": bid, "action": path[0]}

    # 1. Deliver
    if has_active and pos == drop:
        return {"bot": bid, "action": "drop_off"}

    # 2. Head to drop-off if full or collected everything
    if has_active and (len(inv) >= 3 or not still_to_get):
        p = nav(drop, 'to')
        if p is not None:
            return {"bot": bid, "action": p[0] if p else "drop_off"}
        return {"bot": bid, "action": "wait"}

    # 3. Pick up next item
    if still_to_get:
        target = still_to_get[0]
        tx, ty = target["position"]
        if abs(tx-pos[0])+abs(ty-pos[1]) == 1:
            return {"bot": bid, "action": "pick_up", "item_id": target["id"]}
        return act(nav((tx, ty), 'adj'))

    # 4. Fallback deliver
    if has_active:
        p = nav(drop, 'to')
        return {"bot": bid, "action": p[0] if p else "drop_off"}

    # 5. Zero idle: if no assignment and no active items, move toward drop-off
    #    (keeps bot from blocking aisles and positions it centrally)
    p = nav(drop, 'to')
    if p:
        return {"bot": bid, "action": p[0]}

    return {"bot": bid, "action": "wait"}


# ===========================================================================
# Main loop
# ===========================================================================

async def play():
    global _assignments, _last_sig, _dc
    print(f"Connecting: {WS_URL}")
    async with websockets.connect(WS_URL) as ws:
        print("Connected.")
        while True:
            msg = json.loads(await ws.recv())
            print(msg)
            if msg["type"] == "game_over":
                print(f"\nGAME OVER | Score: {msg['score']}")
                break

            state  = msg
            rnd    = state.get("round", "?")
            bots   = state["bots"]
            items  = state["items"]
            drop   = state["drop_off"]
            width  = state["grid"]["width"]
            height = state["grid"]["height"]

            print(f"\n--- Round {rnd}/{state.get('max_rounds','?')} | Score: {state.get('score',0)} ---")

            if rnd == 0:
                _dc.clear()
                _assignments = {}
                _last_sig = None

            shelves  = [i["position"] for i in items if i["position"] != drop]
            wall_set = set(map(tuple, state["grid"]["walls"] + shelves))

            refresh(bots, state, wall_set)
            action_map = decide_all(bots, state, wall_set)

            actions = [action_map[b["id"]] for b in sorted(bots, key=lambda b: b["id"])]
            for bot in sorted(bots, key=lambda b: b["id"]):
                a = action_map[bot["id"]]
                print(f"  bot{bot['id']} {bot['position']} inv={bot['inventory']} -> {a['action']}"
                      + (f" {a.get('item_id','')}" if a['action']=='pick_up' else ""))

            await ws.send(json.dumps({"actions": actions}))


if __name__ == "__main__":
    asyncio.run(play())
