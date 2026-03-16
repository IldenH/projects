import asyncio
import json
import os
import websockets
from itertools import permutations

WS_URL = os.environ.get("WS_URL", "wss://game-dev.ainm.no/ws?token=YOUR_TOKEN_HERE")


# ---------------------------------------------------------------------------
# BFS primitives
# ---------------------------------------------------------------------------

def bfs_path_to_adjacent(start, goal, wall_set, width, height):
    """Path to any cell adjacent to goal (for item pickup). Returns [] if already adjacent.
    Deterministic: ties broken by (x, y) so same path is always chosen."""
    sx, sy = int(start[0]), int(start[1])
    gx, gy = int(goal[0]), int(goal[1])
    if abs(sx - gx) + abs(sy - gy) == 1:
        return []
    # BFS but store (dist, x, y, path) and use heap for deterministic tie-breaking
    import heapq
    heap = [(0, sx, sy, [])]
    visited = {(sx, sy)}
    dirs = [("move_up",0,-1),("move_down",0,1),("move_left",-1,0),("move_right",1,0)]
    while heap:
        dist, cx, cy, path = heapq.heappop(heap)
        for act, dx, dy in dirs:
            nx, ny = cx+dx, cy+dy
            if not (0<=nx<width and 0<=ny<height): continue
            if (nx,ny) in wall_set or (nx,ny) in visited: continue
            np = path + [act]
            if abs(nx-gx)+abs(ny-gy) == 1: return np
            visited.add((nx,ny))
            heapq.heappush(heap, (dist+1, nx, ny, np))
    return None


def bfs_path_to(start, goal, wall_set, width, height):
    """Path to walk onto goal cell. Returns [] if already there.
    Deterministic: ties broken by (x, y)."""
    import heapq
    sx, sy = int(start[0]), int(start[1])
    gx, gy = int(goal[0]), int(goal[1])
    if (sx,sy)==(gx,gy): return []
    heap = [(0, sx, sy, [])]
    visited = {(sx,sy)}
    dirs = [("move_up",0,-1),("move_down",0,1),("move_left",-1,0),("move_right",1,0)]
    while heap:
        dist, cx, cy, path = heapq.heappop(heap)
        for act, dx, dy in dirs:
            nx, ny = cx+dx, cy+dy
            if not (0<=nx<width and 0<=ny<height): continue
            if (nx,ny) in wall_set or (nx,ny) in visited: continue
            np = path + [act]
            if (nx,ny)==(gx,gy): return np
            visited.add((nx,ny))
            heapq.heappush(heap, (dist+1, nx, ny, np))
    return None


def dist_adj(a, b, wall_set, width, height):
    p = bfs_path_to_adjacent(a, b, wall_set, width, height)
    return len(p) if p is not None else 999999

def dist_to(a, b, wall_set, width, height):
    p = bfs_path_to(a, b, wall_set, width, height)
    return len(p) if p is not None else 999999


# ---------------------------------------------------------------------------
# Distance cache — BFS is expensive, cache all pairwise distances
# ---------------------------------------------------------------------------
_dist_cache = {}  # (start, goal, mode) -> int   mode: 'adj' or 'to'

def cdist_adj(a, b, wall_set, width, height):
    key = (tuple(a), tuple(b), 'adj')
    if key not in _dist_cache:
        _dist_cache[key] = dist_adj(a, b, wall_set, width, height)
    return _dist_cache[key]

def cdist_to(a, b, wall_set, width, height):
    key = (tuple(a), tuple(b), 'to')
    if key not in _dist_cache:
        _dist_cache[key] = dist_to(a, b, wall_set, width, height)
    return _dist_cache[key]


# ---------------------------------------------------------------------------
# Multi-trip planner
# Splits items into batches of ≤3, finds optimal batch order and sequence
# that minimises total rounds: sum of all travel + pickup steps across all trips
# ---------------------------------------------------------------------------

def plan_all_trips(start, items, drop_off, wall_set, width, height):
    """
    Returns a list of trips, each trip = list of item dicts.
    Optimises total cost: for each possible way to split items into trips of ≤3,
    find the ordering that minimises total travel distance across all trips.
    Since easy orders are 3-4 items max, we have at most 2 trips.
    """
    if not items:
        return []

    n = len(items)

    # For 1-3 items: single trip, just TSP
    if n <= 3:
        seq = _tsp_trip(tuple(start), items, tuple(drop_off), wall_set, width, height)
        return [seq]

    # For 4 items: try all splits into (3,1) and (2,2), pick cheapest total
    best_cost = None
    best_plan = None

    # Split options: which items go in trip 1 (size 3 or 2)
    from itertools import combinations
    for trip1_size in [3, 2]:
        for trip1_indices in combinations(range(n), trip1_size):
            trip2_indices = [i for i in range(n) if i not in trip1_indices]
            trip1 = [items[i] for i in trip1_indices]
            trip2 = [items[i] for i in trip2_indices]

            seq1 = _tsp_trip(tuple(start), trip1, tuple(drop_off), wall_set, width, height)
            # Trip 2 starts from drop-off (after delivering trip 1)
            seq2 = _tsp_trip(tuple(drop_off), trip2, tuple(drop_off), wall_set, width, height)

            cost = _trip_cost(tuple(start), seq1, tuple(drop_off), wall_set, width, height)
            cost += _trip_cost(tuple(drop_off), seq2, tuple(drop_off), wall_set, width, height)

            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_plan = [seq1, seq2]

    return best_plan


def _tsp_trip(start, items, drop_off, wall_set, width, height):
    """Optimal ordering of items for a single trip, minimising travel + return to drop-off."""
    if len(items) == 1:
        return list(items)
    best_cost, best_order = None, None
    for perm in permutations(items):
        cost = _trip_cost(start, list(perm), drop_off, wall_set, width, height)
        if best_cost is None or cost < best_cost:
            best_cost, best_order = cost, list(perm)
    return best_order


def _trip_cost(start, seq, drop_off, wall_set, width, height):
    cost = 0
    cur = tuple(start)
    for item in seq:
        ipos = tuple(item["position"])
        cost += cdist_adj(cur, ipos, wall_set, width, height)
        cur = ipos
    cost += cdist_to(cur, tuple(drop_off), wall_set, width, height)
    return cost


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_needed_types(order):
    if not order: return []
    needed = list(order["items_required"])
    for d in order["items_delivered"]:
        if d in needed: needed.remove(d)
    return needed


def match_items(needed_types, items_on_map):
    result, used = [], set()
    for t in needed_types:
        for item in items_on_map:
            if item["type"] == t and item["id"] not in used:
                result.append(item)
                used.add(item["id"])
                break
    return result



# ---------------------------------------------------------------------------
# Move validator — sanity-check that an action won't walk into a wall
# ---------------------------------------------------------------------------
_ACTION_DELTAS = {
    "move_up":    (0, -1),
    "move_down":  (0,  1),
    "move_left":  (-1, 0),
    "move_right": (1,  0),
}

def validate_move(action, pos, wall_set, width, height):
    """Return True if action leads to a valid (non-wall, in-bounds) cell."""
    if action not in _ACTION_DELTAS:
        return True  # pick_up, drop_off, wait are always structurally valid
    dx, dy = _ACTION_DELTAS[action]
    nx, ny = pos[0]+dx, pos[1]+dy
    if not (0 <= nx < width and 0 <= ny < height):
        return False
    if (nx, ny) in wall_set:
        return False
    return True

# ---------------------------------------------------------------------------
# Global plan state
# ---------------------------------------------------------------------------
_plan_order_id = None
_plan_trips = []        # list of trips (each trip = list of item dicts)
_plan_item_ids = None   # frozenset — invalidate when items change


def get_plan(order_id, bot_pos, still_items, drop_off, wall_set, width, height):
    global _plan_order_id, _plan_trips, _plan_item_ids

    current_ids = frozenset(i["id"] for i in still_items)

    # Invalidate if order changed or item set changed
    if _plan_order_id != order_id or _plan_item_ids != current_ids:
        _plan_trips = plan_all_trips(bot_pos, still_items, drop_off, wall_set, width, height)
        _plan_order_id = order_id
        _plan_item_ids = current_ids

    # Filter trips to only contain items still on map
    live_ids = {i["id"] for i in still_items}
    _plan_trips = [[i for i in trip if i["id"] in live_ids] for trip in _plan_trips]
    _plan_trips = [t for t in _plan_trips if t]  # remove empty trips

    return _plan_trips


# ---------------------------------------------------------------------------
# Main decision function
# ---------------------------------------------------------------------------

def next_action(bot, state):
    round_num = state.get("round", "?")
    x, y = bot["position"]
    pos = (x, y)
    inventory = bot["inventory"]
    drop_off = state["drop_off"]
    grid_walls = state["grid"]["walls"]
    width  = state["grid"]["width"]
    height = state["grid"]["height"]
    items_on_map = state["items"]

    shelf_positions = [i["position"] for i in items_on_map if i["position"] != drop_off]
    wall_set = set(map(tuple, grid_walls + shelf_positions))

    active_order = next((o for o in state["orders"] if o["status"] == "active"), None)
    preview_order = next((o for o in state["orders"] if o["status"] == "preview"), None)

    needed_types = get_needed_types(active_order)
    has_active_items = any(t in inventory for t in needed_types)

    inv_copy = list(inventory)
    still_needed_types = []
    for t in needed_types:
        if t in inv_copy: inv_copy.remove(t)
        else: still_needed_types.append(t)

    still_items = match_items(still_needed_types, items_on_map)

    print(f"\n  [R{round_num}] pos={list(pos)} inv={inventory} drop_off={drop_off}")
    print(f"  [R{round_num}] active={active_order['id'] if active_order else None} "
          f"needed={needed_types} still={[(i['type'],i['position']) for i in still_items]}")

    # ------------------------------------------------------------------
    # 1. At drop-off with active items → deliver
    # ------------------------------------------------------------------
    if has_active_items and list(pos) == drop_off:
        print(f"  [R{round_num}] -> drop_off")
        return {"bot": bot["id"], "action": "drop_off"}

    # ------------------------------------------------------------------
    # 2. Get multi-trip plan
    # ------------------------------------------------------------------
    if still_items and active_order:
        trips = get_plan(active_order["id"], pos, still_items, drop_off, wall_set, width, height)
        print(f"  [R{round_num}] trips={[[( i['type'],i['position']) for i in t] for t in trips]}")

        if trips:
            current_trip = trips[0]

            # Carrying items from this trip already → check if we have all of them
            trip_types = [i["type"] for i in current_trip]
            inv_copy2 = list(inventory)
            trip_still_needed = []
            for t in trip_types:
                if t in inv_copy2: inv_copy2.remove(t)
                else: trip_still_needed.append(t)

            trip_still_items = match_items(trip_still_needed, items_on_map)

            # Have everything for this trip → deliver
            inv_has_trip = len(trip_still_items) == 0 and has_active_items
            if len(inventory) >= 3 or inv_has_trip:
                path = bfs_path_to(pos, tuple(drop_off), wall_set, width, height)
                action = path[0] if path else "drop_off"
                if action and not validate_move(action, pos, wall_set, width, height):
                    print(f"  [R{round_num}] WARNING: invalid move {action} from {list(pos)}, recomputing")
                    _dist_cache.clear()
                    path = bfs_path_to(pos, tuple(drop_off), wall_set, width, height)
                    action = path[0] if path else "drop_off"
                print(f"  [R{round_num}] -> {action} (delivering trip, dist={len(path) if path else 0})")
                return {"bot": bot["id"], "action": action}

            # Go pick up next item in this trip
            if trip_still_items:
                target = trip_still_items[0]
                tx, ty = target["position"]

                if abs(tx-x)+abs(ty-y) == 1:
                    print(f"  [R{round_num}] -> pick_up {target['id']} ({target['type']})")
                    return {"bot": bot["id"], "action": "pick_up", "item_id": target["id"]}

                path = bfs_path_to_adjacent(pos, (tx,ty), wall_set, width, height)
                action = path[0] if path else None
                if action and not validate_move(action, pos, wall_set, width, height):
                    print(f"  [R{round_num}] WARNING: invalid move {action} from {list(pos)}, wall_set mismatch — clearing dist cache")
                    _dist_cache.clear()
                    path = bfs_path_to_adjacent(pos, (tx,ty), wall_set, width, height)
                    action = path[0] if path else None
                print(f"  [R{round_num}] -> {action} (toward {target['type']} @ {target['position']}, {len(path) if path else '?'} steps)")
                if action:
                    return {"bot": bot["id"], "action": action}

    # ------------------------------------------------------------------
    # 3. Have active items but no more to collect → deliver
    # ------------------------------------------------------------------
    if has_active_items:
        path = bfs_path_to(pos, tuple(drop_off), wall_set, width, height)
        action = path[0] if path else "drop_off"
        print(f"  [R{round_num}] -> {action} (deliver remaining active items)")
        return {"bot": bot["id"], "action": action}

    # ------------------------------------------------------------------
    # 4. Pre-fetch preview items when inventory has space
    # ------------------------------------------------------------------
    if preview_order and len(inventory) < 3:
        preview_types = get_needed_types(preview_order)
        inv_copy3 = list(inventory)
        # Don't count items we already have for active order
        for t in needed_types:
            if t in inv_copy3: inv_copy3.remove(t)
        preview_still = []
        for t in preview_types:
            if t in inv_copy3: inv_copy3.remove(t)
            elif len(preview_still) + len(inventory) < 3: preview_still.append(t)

        preview_items = match_items(preview_still, items_on_map)
        if preview_items:
            seq = _tsp_trip(pos, preview_items[:3-len(inventory)], tuple(drop_off), wall_set, width, height)
            if seq:
                target = seq[0]
                tx, ty = target["position"]
                if abs(tx-x)+abs(ty-y) == 1:
                    print(f"  [R{round_num}] -> pick_up {target['id']} (preview prefetch)")
                    return {"bot": bot["id"], "action": "pick_up", "item_id": target["id"]}
                path = bfs_path_to_adjacent(pos, (tx,ty), wall_set, width, height)
                if path:
                    print(f"  [R{round_num}] -> {path[0]} (preview prefetch {target['type']})")
                    return {"bot": bot["id"], "action": path[0]}

    print(f"  [R{round_num}] -> wait")
    return {"bot": bot["id"], "action": "wait"}


# ---------------------------------------------------------------------------
# WebSocket loop
# ---------------------------------------------------------------------------

async def play():
    print(f"Connecting to: {WS_URL}")
    async with websockets.connect(WS_URL) as ws:
        print("Connected.")
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "game_over":
                print(f"\n{'='*50}\nGAME OVER | Final Score: {msg['score']}")
                break
            state = msg
            print(f"\n{'='*50}\nRound {state.get('round','?')}/{state.get('max_rounds','?')} "
                  f"| Score: {state.get('score',0)}")
            actions = [next_action(bot, state) for bot in state["bots"]]
            print(f"  >> Sending: {actions}")
            await ws.send(json.dumps({"actions": actions}))


if __name__ == "__main__":
    asyncio.run(play())
