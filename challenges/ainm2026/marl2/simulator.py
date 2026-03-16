"""
simulator.py — Offline grocery-store simulator for training without hitting the live server.

Two modes:
  1. REPLAY mode  — iterate over recorded .json.gz replay files.
  2. SYNTHETIC mode — procedurally generate store layouts that match each difficulty tier,
                      then simulate full episodes locally (no server needed at all).

The simulator exposes a gym-like API:
    env = GroceryEnv(difficulty="medium")
    obs = env.reset()
    while not done:
        actions = agent.act(obs)
        obs, reward, done, info = env.step(actions)
"""

from __future__ import annotations

import copy
import gzip
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

try:
    from hardcoded_maps import HARDCODED_MAPS
except ImportError:
    HARDCODED_MAPS = {}


# ---------------------------------------------------------------------------
# Difficulty configs
# ---------------------------------------------------------------------------

DIFFICULTY = {
    "easy":   dict(width=12, height=10, n_bots=1,  n_aisles=2, n_item_types=4,  order_min=3, order_max=4),
    "medium": dict(width=16, height=12, n_bots=3,  n_aisles=3, n_item_types=8,  order_min=3, order_max=5),
    "hard":   dict(width=22, height=14, n_bots=5,  n_aisles=4, n_item_types=12, order_min=3, order_max=5),
    "expert": dict(width=28, height=18, n_bots=10, n_aisles=5, n_item_types=16, order_min=4, order_max=6),
}

ITEM_NAMES = [
    "apples", "bananas", "bread", "butter", "cereal", "cheese", "cream",
    "eggs", "flour", "milk", "oats", "onions", "pasta", "rice", "tomatoes", "yogurt",
]

MAX_ROUNDS = 300
MAX_INVENTORY = 3
DEFAULT_TOTAL_ORDERS = 50
ORDER_COMPLETION_REWARD_BONUS = 20.0


# ---------------------------------------------------------------------------
# Map generation
# ---------------------------------------------------------------------------

def generate_map(cfg: dict, seed: int = 42) -> dict:
    """
    Build a grocery store layout matching the real server's map style.

    Layout (vertical aisles, like a real supermarket):
    - Shelf columns run top-to-bottom, with walkway aisles between them.
    - Each shelf column is 2 cells wide (both sides of an aisle).
    - Shelves leave a 1-cell gap at top and bottom for the perimeter walkway.
    - Drop-off near bottom-left.
    - Bots start on the bottom walkway.

    This produces ~50 walls on easy (12x10) matching the real server.
    Randomisation across seeds ensures the agent sees diverse layouts.
    """
    rng = random.Random(seed)
    W, H = cfg["width"], cfg["height"]
    n_aisles = cfg["n_aisles"]
    n_bots   = cfg["n_bots"]
    n_types  = cfg["n_item_types"]
    active_item_names = ITEM_NAMES[:n_types]

    walls: list[list[int]] = []
    item_cells: list[list[int]] = []

    # Vertical shelf columns: place n_aisles shelf-pairs across the width.
    # Each aisle occupies 3 columns: [shelf | walkway | shelf]
    # Walkways also run along x=0 and x=W-1 (perimeter).
    # Leave rows 0 and H-1 as clear perimeter walkways.

    # Distribute shelf column-pairs evenly across interior width
    # with a random offset per seed for diversity
    usable_w = W - 2  # exclude perimeter columns
    aisle_spacing = usable_w // (n_aisles + 1)

    shelf_col_pairs: list[tuple[int, int]] = []  # (left_shelf_x, right_shelf_x)
    for i in range(1, n_aisles + 1):
        cx = 1 + i * aisle_spacing
        # Randomise position slightly
        cx += rng.randint(-1, 1)
        cx = max(2, min(W - 3, cx))
        left_x  = cx - 1
        right_x = cx + 1
        if left_x >= 1 and right_x <= W - 2:
            shelf_col_pairs.append((left_x, right_x))

    # Shelf cells: full column height except top row (0), bottom 2 rows, and
    # one random internal gap per column for passage
    for left_x, right_x in shelf_col_pairs:
        for shelf_x in (left_x, right_x):
            # Random gap position — ensures connectivity
            gap_y = rng.randint(2, H - 3)
            for y in range(1, H - 2):
                if y == gap_y:
                    continue  # walkway gap through shelf
                walls.append([shelf_x, y])
                item_cells.append([shelf_x, y])

    # Ensure all walkable cells are reachable (basic connectivity check)
    # If not, fall back to simple horizontal layout
    wall_set = set(map(tuple, walls))
    walkable = {(x, y) for x in range(W) for y in range(H) if (x, y) not in wall_set}
    drop_off_pos = (1, H - 2)

    # BFS from drop-off to check connectivity
    from collections import deque
    visited = {drop_off_pos}
    q = deque([drop_off_pos])
    while q:
        cx, cy = q.popleft()
        for nx, ny in [(cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)]:
            if (nx, ny) in walkable and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny))

    # If more than 20% of walkable cells are unreachable, fall back to simple layout
    if len(visited) < 0.8 * len(walkable):
        walls = []
        item_cells = []
        wall_set = set()
        step = (H - 2) // (n_aisles + 1)
        for i in range(1, n_aisles + 1):
            row = 1 + i * step
            if row < H - 1:
                gap = rng.randint(1, W - 2)
                for x in range(1, W - 1):
                    if x != gap:
                        walls.append([x, row])
                        item_cells.append([x, row])
        wall_set = set(map(tuple, walls))

    # Place items on shelf cells — one item type per cell, cycling through types
    items = []
    rng.shuffle(item_cells)
    # Deduplicate item_cells (both sides of shelf share same position sometimes)
    seen_cells: set[tuple] = set()
    unique_item_cells = []
    for c in item_cells:
        k = tuple(c)
        if k not in seen_cells:
            seen_cells.add(k)
            unique_item_cells.append(c)

    for idx, cell in enumerate(unique_item_cells):
        itype = active_item_names[idx % n_types]
        items.append({
            "id":       f"item_{idx}",
            "type":     itype,
            "position": cell,
        })

    # Bots start on the bottom walkway row (H-1), spread across width
    bot_xs = sorted(rng.sample(range(1, W - 1), min(n_bots, W - 2)))
    bots = [
        {"id": i, "position": [bot_xs[i], H - 1], "inventory": []}
        for i in range(n_bots)
    ]

    drop_off = [1, H - 2]

    return {
        "grid":      {"width": W, "height": H, "walls": walls},
        "bots":      bots,
        "items":     items,
        "drop_off":  drop_off,
        "_wall_set": set(map(tuple, walls)),
    }


def get_hardcoded_map(difficulty: str) -> dict:
    """Return a deep-copied hardcoded map for the given difficulty."""
    if difficulty not in HARDCODED_MAPS:
        raise ValueError(
            f"No hardcoded map found for difficulty '{difficulty}'. "
            "Run get_maps.py to regenerate hardcoded_maps.py."
        )
    m = copy.deepcopy(HARDCODED_MAPS[difficulty])
    if "_wall_set" not in m:
        m["_wall_set"] = set(map(tuple, m["grid"]["walls"]))
    return m


def generate_order(item_types: list[str], min_items: int, max_items: int, rng: random.Random) -> dict:
    size = rng.randint(min_items, max_items)
    required = rng.choices(item_types, k=size)
    return {
        "id": f"order_{rng.randint(0, 99999)}",
        "items_required": required,
        "items_delivered": [],
        "complete": False,
        "status": "active",
    }


# ---------------------------------------------------------------------------
# Offline Environment
# ---------------------------------------------------------------------------

class GroceryEnv:
    """
    Offline grocery-store environment.

    Observation (per bot, flattened):
      - bot position (2)
      - inventory one-hot over all item types (16)
      - nearest needed item direction + distance (3)
      - drop-off direction + distance (3)
      - active order progress (1)
      Total: 2 + 16 + 3 + 3 + 1 = 25 per bot

    Actions (discrete, per bot): 0=up 1=down 2=left 3=right 4=pick_up 5=drop_off 6=wait
    """

    ACTION_NAMES = ["move_up", "move_down", "move_left", "move_right", "pick_up", "drop_off", "wait"]
    N_ACTIONS = 7

    def __init__(
        self,
        difficulty: str = "medium",
        seed: int | None = None,
        map_source: str = "hardcoded",
        order_source: str = "replay",
    ):
        self.difficulty = difficulty
        self.cfg = DIFFICULTY[difficulty]
        if map_source not in ("hardcoded", "synthetic"):
            raise ValueError(f"Invalid map_source='{map_source}'. Use 'hardcoded' or 'synthetic'.")
        if order_source not in ("replay", "synthetic"):
            raise ValueError(f"Invalid order_source='{order_source}'. Use 'replay' or 'synthetic'.")
        self.map_source = map_source
        self.order_source = order_source
        self.block_item_cells = True
        self.n_item_types = self.cfg["n_item_types"]
        self.n_bots = self.cfg["n_bots"]
        # obs: pos(2) + inv(16, all ITEM_NAMES) + target_dir(3) + ao_pickup_dir(3) = 24
        self.obs_dim = 24
        self.seed = seed if seed is not None else random.randint(0, 2**31)
        self._rng = random.Random(self.seed)
        self._map: dict = {}
        self._state: dict = {}
        self._round = 0
        self._score = 0
        self._order_counter = 0
        self._total_orders = DEFAULT_TOTAL_ORDERS
        self._item_types: list[str] = ITEM_NAMES[:self.n_item_types]

    # ------------------------------------------------------------------
    def reset(self) -> list[list[float]]:
        self._rng = random.Random(self.seed)
        if self.map_source == "hardcoded":
            self._map = get_hardcoded_map(self.difficulty)
        else:
            self._map = generate_map(self.cfg, self.seed)
        self._round = 0
        self._score = 0
        self._order_counter = 0
        self._total_orders = DEFAULT_TOTAL_ORDERS

        self._bots = copy.deepcopy(self._map["bots"])
        self._items = copy.deepcopy(self._map["items"])
        self._wall_set: set[tuple[int, int]] = set(self._map["_wall_set"])
        # Mirror live server movement: shelf/item cells are blocked.
        shelf_set = {tuple(item["position"]) for item in self._items}
        self._wall_set |= shelf_set
        W, H = self._map["grid"]["width"], self._map["grid"]["height"]

        if self.map_source == "hardcoded":
            # Replay maps may use a different item subset/order than ITEM_NAMES[:n_item_types].
            # Restrict order sampling to item types that actually exist on this map.
            seen: set[str] = set()
            self._item_types = []
            for item in self._items:
                t = item["type"]
                if t not in seen:
                    seen.add(t)
                    self._item_types.append(t)
            if not self._item_types:
                raise ValueError(f"No item types found in hardcoded map for '{self.difficulty}'.")
        else:
            self._item_types = ITEM_NAMES[:self.n_item_types]

        if len(self._bots) != self.n_bots:
            raise ValueError(
                f"Map bot count ({len(self._bots)}) does not match DIFFICULTY['{self.difficulty}'] "
                f"n_bots ({self.n_bots})."
            )

        # Precompute approach cache: item_id -> {pos -> (next_step, dist)}
        self._approach_cache: dict[str, dict] = {}
        for item in self._items:
            self._approach_cache[item["id"]] = precompute_item_approach(
                tuple(item["position"]), self._wall_set, W, H
            )

        # Precompute drop-off BFS cache: pos -> (next_step, dist)
        self._drop_cache: dict[tuple, tuple] = self._build_drop_cache()

        # Precompute from-item BFS: item_id -> {pos: dist_from_item_neighbors}
        # Enables correct inter-item routing for TSP planning.
        self._from_item_cache: dict[str, dict] = {}
        for item in self._items:
            self._from_item_cache[item["id"]] = self._build_from_item_dist(
                tuple(item["position"])
            )
        replay_orders = (
            self._load_initial_orders_from_replay()
            if self.order_source == "replay"
            else None
        )
        if replay_orders:
            self._orders = replay_orders
            self._order_counter = max(
                (
                    int(str(o["id"]).split("_")[-1])
                    for o in self._orders
                    if str(o.get("id", "")).startswith("order_")
                ),
                default=1,
            )
        else:
            active = self._new_order("active")
            preview = self._new_order("preview")
            self._orders = [active, preview]

        return self._get_obs()

    def _load_initial_orders_from_replay(self) -> list[dict] | None:
        if self.map_source != "hardcoded":
            return None
        replay_path = Path("replays") / f"{self.difficulty}.json.gz"
        if not replay_path.exists():
            return None
        try:
            with gzip.open(replay_path, "rt", encoding="utf-8") as f:
                payload = json.load(f)
            traj = payload.get("trajectory", [])
            if not traj:
                return None
            state0 = traj[0].get("state", {})
            orders = state0.get("orders")
            if not isinstance(orders, list) or not orders:
                return None
            self._total_orders = int(state0.get("total_orders", DEFAULT_TOTAL_ORDERS))
            return copy.deepcopy(orders)
        except Exception:
            return None

    def _build_from_item_dist(self, shelf_pos: tuple) -> dict:
        """BFS outward from walkable neighbors of shelf_pos -> {pos: dist}."""
        from collections import deque
        W, H = self.cfg["width"], self.cfg["height"]
        dist: dict = {}; queue: deque = deque()
        x, y = shelf_pos
        for nx, ny in [(x,y-1),(x,y+1),(x-1,y),(x+1,y)]:
            npos = (nx, ny)
            if 0<=nx<W and 0<=ny<H and npos not in self._wall_set:
                dist[npos] = 1; queue.append(npos)
        while queue:
            pos = queue.popleft(); px, py = pos
            for nx, ny in [(px,py-1),(px,py+1),(px-1,py),(px+1,py)]:
                npos = (nx, ny)
                if npos in dist or not(0<=nx<W and 0<=ny<H) or npos in self._wall_set: continue
                dist[npos] = dist[pos] + 1; queue.append(npos)
        return dist

    def plan_route(self, items_to_pick: list, start_pos: tuple) -> list:
        """
        TSP: find pickup order minimising start->item1->...->itemN->dropoff.
        Uses exact BFS distances from _from_item_cache. O(N!) but N<=3.
        """
        import itertools
        if len(items_to_pick) <= 1:
            return list(items_to_pick)
        W, H = self.cfg["width"], self.cfg["height"]

        def neighbor_after_pickup(item, approach_from):
            """Walkable neighbor of shelf we end up at after picking up item."""
            shelf = tuple(item["position"])
            best_n, best_d = approach_from, 9999
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                n = (shelf[0]+dx, shelf[1]+dy)
                if not (0<=n[0]<W and 0<=n[1]<H) or n in self._wall_set:
                    continue
                # distance from approach_from to this neighbor
                fc = self._from_item_cache.get(item["id"], {})
                d = fc.get(approach_from, 9999)
                if d < best_d:
                    best_d = d; best_n = n
            return best_n

        best_cost = float("inf"); best_perm = list(items_to_pick)
        for perm in itertools.permutations(items_to_pick):
            pos = start_pos; total = 0
            for item in perm:
                fc = self._from_item_cache.get(item["id"], {})
                d = fc.get(pos, 9999)
                if d >= 9999: total = float("inf"); break
                total += d
                pos = neighbor_after_pickup(item, pos)
            drop_e = self._drop_cache.get(pos)
            total += drop_e[1] if drop_e else 9999
            if total < best_cost:
                best_cost = total; best_perm = list(perm)
        return best_perm

    def _build_drop_cache(self) -> dict[tuple[int,int], tuple[tuple[int,int], int]]:
        """BFS outward from drop-off: pos -> (first_step_toward_dropoff, dist)."""
        from collections import deque
        drop = tuple(self._map["drop_off"])
        W, H = self.cfg["width"], self.cfg["height"]
        dist: dict = {drop: 0}
        parent: dict = {drop: drop}
        queue: deque = deque([drop])
        while queue:
            pos = queue.popleft()
            x, y = pos
            for nx, ny in [(x,y-1),(x,y+1),(x-1,y),(x+1,y)]:
                npos = (nx, ny)
                if npos in dist: continue
                if not (0<=nx<W and 0<=ny<H): continue
                if npos in self._wall_set: continue
                dist[npos] = dist[pos] + 1
                parent[npos] = pos
                queue.append(npos)

        # First step from pos toward drop-off is simply parent[pos].
        return {pos: (parent[pos], dist[pos]) for pos in dist}

    # ------------------------------------------------------------------
    def step(self, actions: list[int]) -> tuple[list[list[float]], float, bool, dict]:
        """
        actions: list of int, one per bot (index into ACTION_NAMES).
        Returns: obs, reward, done, info
        """
        assert len(actions) == self.n_bots

        prev_state = self.get_state_dict()

        # Process each bot's action in bot-list order, matching replay transition order.
        occupied_counts: dict[tuple[int, int], int] = {}
        for b in self._bots:
            p = tuple(b["position"])
            occupied_counts[p] = occupied_counts.get(p, 0) + 1
        dropping_bot_ids: set[int] = set()
        for bot, action_idx in zip(self._bots, actions):
            action = self.ACTION_NAMES[action_idx]
            if action == "drop_off":
                dropping_bot_ids.add(bot["id"])
            self._apply_action(bot, action, occupied_counts)
        self._process_deliveries(dropping_bot_ids)

        self._round += 1
        done = self._round >= MAX_ROUNDS

        curr_state = self.get_state_dict()
        reward = _compute_replay_style_reward(prev_state, curr_state)
        score_delta = self._score - prev_state["score"]

        info = {
            "round": self._round,
            "score": self._score,
            "score_delta": score_delta,
        }

        return self._get_obs(), reward, done, info

    # ------------------------------------------------------------------
    def get_state_dict(self) -> dict:
        """Return a full game-state dict matching the server format."""
        active_idx = next((i for i, o in enumerate(self._orders) if o.get("status") == "active"), 0)
        return {
            "type": "game_state",
            "round": self._round,
            "max_rounds": MAX_ROUNDS,
            "grid": self._map["grid"],
            "bots": copy.deepcopy(self._bots),
            "items": copy.deepcopy(self._items),
            "orders": copy.deepcopy(self._orders),
            "drop_off": self._map["drop_off"],
            "score": self._score,
            "active_order_index": active_idx,
            "total_orders": self._total_orders,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _new_order(self, status: str) -> dict:
        order = generate_order(
            self._item_types,
            self.cfg["order_min"],
            self.cfg["order_max"],
            self._rng,
        )
        order["id"] = f"order_{self._order_counter}"
        order["status"] = status
        self._order_counter += 1
        return order

    def _apply_action(
        self,
        bot: dict,
        action: str,
        occupied_counts: dict[tuple[int, int], int] | None = None,
    ) -> None:
        x, y = bot["position"]
        W, H = self.cfg["width"], self.cfg["height"]
        dx, dy = 0, 0

        if action == "move_up":    dy = -1
        elif action == "move_down": dy = 1
        elif action == "move_left": dx = -1
        elif action == "move_right": dx = 1
        elif action == "pick_up":
            self._try_pick_up(bot)
            return
        elif action == "drop_off":
            return  # delivery handled by _process_deliveries() in step()
        elif action == "wait":
            return

        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H:
            target = (nx, ny)
            source = (x, y)
            blocked_by_bot = occupied_counts is not None and occupied_counts.get(target, 0) > 0
            if (nx, ny) not in self._wall_set and not blocked_by_bot:
                if occupied_counts is not None:
                    occupied_counts[source] = max(0, occupied_counts.get(source, 0) - 1)
                    occupied_counts[target] = occupied_counts.get(target, 0) + 1
                bot["position"] = [nx, ny]

    def _try_pick_up(self, bot: dict) -> None:
        """
        Items are infinite shelves — picking up adds to inventory but the
        shelf item stays on the map with the same id and position forever.
        The server never removes items from state["items"].
        """
        if len(bot["inventory"]) >= MAX_INVENTORY:
            return
        bx, by = bot["position"]
        active  = next((o for o in self._orders if o["status"] == "active"),  None)
        preview = next((o for o in self._orders if o["status"] == "preview"), None)
        needed_active  = _needed_types(active)
        needed_preview = _needed_types(preview)
        all_needed     = set(needed_active + needed_preview)

        adjacent = [
            item for item in self._items
            if abs(item["position"][0] - bx) + abs(item["position"][1] - by) == 1
        ]
        if not adjacent:
            return

        # Only pick up items that are needed — never pollute inventory
        wanted = [i for i in adjacent if i["type"] in all_needed]
        if not wanted:
            return

        # Prefer active order items over preview items
        active_wanted = [i for i in wanted if i["type"] in set(needed_active)]
        item = (active_wanted or wanted)[0]
        # Shelf is infinite — just add to inventory, item stays on map
        bot["inventory"].append(item["type"])

    def _process_deliveries(self, dropping_bot_ids: set[int]) -> None:
        if not dropping_bot_ids:
            return
        drop_x, drop_y = self._map["drop_off"]
        active = next((o for o in self._orders if o["status"] == "active"), None)
        if not active:
            return

        needed = list(active["items_required"])
        for d in active["items_delivered"]:
            if d in needed:
                needed.remove(d)

        for bot in self._bots:
            bx, by = bot["position"]
            if bot["id"] not in dropping_bot_ids:
                continue
            if [bx, by] != [drop_x, drop_y]:
                continue
            kept = []
            for item_type in bot["inventory"]:
                if item_type in needed:
                    needed.remove(item_type)
                    active["items_delivered"].append(item_type)
                    self._score += 1
                else:
                    kept.append(item_type)
            bot["inventory"] = kept

        # Check order complete
        needed_check = list(active["items_required"])
        for d in active["items_delivered"]:
            if d in needed_check:
                needed_check.remove(d)

        if not needed_check:
            active["complete"] = True
            active["status"] = "complete"
            self._score += 5  # order completion bonus

            # Promote preview to active
            for o in self._orders:
                if o["status"] == "preview":
                    o["status"] = "active"
                    break

            # Add new preview
            new_preview = self._new_order("preview")
            self._orders.append(new_preview)

    def _get_obs(self) -> list[list[float]]:
        """
        Per-bot observation (24 features):
          pos (2): normalised x, y
          inv_vec (16): one-hot inventory contents
          target_dir (3): BFS next-step direction+dist toward immediate goal.
                          Matches batched guided policy:
                          - if should deliver (carrying active items & none left to pick,
                            or inv full) → toward drop-off
                          - else → toward next needed item (active order, then preview)
          pickup_dir (3): direction+dist toward nearest active-order item always,
                          so network can see pickup target even while delivering
          Total: 2 + 16 + 3 + 3 = 24
        """
        W, H = self.cfg["width"], self.cfg["height"]
        D = max(W, H)
        active  = next((o for o in self._orders if o["status"] == "active"),  None)
        preview = next((o for o in self._orders if o["status"] == "preview"), None)
        needed_active  = _needed_types(active)
        needed_preview = _needed_types(preview) if preview else []
        needed_set     = set(needed_active)
        type_idx       = {t: i for i, t in enumerate(self._item_types)}

        obs_all = []
        for bot in self._bots:
            bx, by = bot["position"]
            bpos   = (bx, by)
            inv    = bot["inventory"]

            # Normalised position
            pos = [bx / W, by / H]

            # Inventory one-hot — always 16 slots (all ITEM_NAMES) so obs_dim is
            # constant across difficulties and checkpoints are interchangeable
            full_type_idx = {t: i for i, t in enumerate(ITEM_NAMES)}
            inv_vec = [0.0] * len(ITEM_NAMES)
            for itype in inv:
                idx = full_type_idx.get(itype)
                if idx is not None:
                    inv_vec[idx] = min(1.0, inv_vec[idx] + 1.0)

            # Batched policy logic: what items do we still need for active order?
            remaining_active = list(needed_active)
            for i in inv:
                if i in remaining_active:
                    remaining_active.remove(i)
            carrying_active = [i for i in inv if i in needed_set]

            should_deliver = (
                len(inv) >= MAX_INVENTORY
                or (bool(carrying_active) and not remaining_active)
            )

            # Nearest still-needed item (active first, then preview)
            target_types = set(remaining_active)
            if not target_types and needed_preview:
                remaining_preview = list(needed_preview)
                for i in inv:
                    if i in remaining_preview:
                        remaining_preview.remove(i)
                target_types = set(remaining_preview)

            best_dist, best_next = 9999, bpos
            for item in self._items:
                if item["type"] not in target_types:
                    continue
                entry = self._approach_cache.get(item["id"], {}).get(bpos)
                if entry and entry[1] < best_dist:
                    best_dist, best_next = entry[1], entry[0]

            pickup_dir = (
                [(best_next[0]-bx)/D, (best_next[1]-by)/D, best_dist/(W+H)]
                if best_dist < 9999 else [0.0, 0.0, 1.0]
            )

            # Nearest active-order item (always, for reference even while delivering)
            ao_dist, ao_next = 9999, bpos
            for item in self._items:
                if item["type"] not in needed_set:
                    continue
                entry = self._approach_cache.get(item["id"], {}).get(bpos)
                if entry and entry[1] < ao_dist:
                    ao_dist, ao_next = entry[1], entry[0]
            ao_pickup_dir = (
                [(ao_next[0]-bx)/D, (ao_next[1]-by)/D, ao_dist/(W+H)]
                if ao_dist < 9999 else [0.0, 0.0, 1.0]
            )

            # Drop-off direction
            drop_entry    = self._drop_cache.get(bpos)
            drop_dir_vec  = (
                [(drop_entry[0][0]-bx)/D, (drop_entry[0][1]-by)/D, drop_entry[1]/(W+H)]
                if drop_entry else [0.0, 0.0, 1.0]
            )

            # Unified target: direction the bot SHOULD move right now
            target_dir = drop_dir_vec if should_deliver else pickup_dir

            obs_all.append(pos + inv_vec + target_dir + ao_pickup_dir)

        return obs_all


def _needed_types(order: dict | None) -> list[str]:
    if not order:
        return []
    needed = list(order["items_required"])
    for d in order["items_delivered"]:
        if d in needed:
            needed.remove(d)
    return needed


def _compute_replay_style_reward(prev_state: dict | None, curr_state: dict) -> float:
    """Reward aligned with recorder.compute_reward for replay compatibility."""
    if prev_state is None:
        return 0.0

    reward = 0.0
    score_delta = curr_state["score"] - prev_state["score"]
    reward += score_delta * 1.0

    # Extra shaping bonus: strongly reward order completion events.
    prev_completed = sum(1 for o in prev_state.get("orders", []) if o.get("status") == "complete")
    curr_completed = sum(1 for o in curr_state.get("orders", []) if o.get("status") == "complete")
    completed_delta = max(0, curr_completed - prev_completed)
    reward += completed_delta * ORDER_COMPLETION_REWARD_BONUS

    prev_inv = sum(len(b["inventory"]) for b in prev_state["bots"])
    curr_inv = sum(len(b["inventory"]) for b in curr_state["bots"])
    items_picked = max(0, curr_inv - prev_inv)
    reward += items_picked * 0.2

    idle = sum(1 for b in curr_state["bots"] if not b["inventory"])
    reward -= idle * 0.05

    return round(reward, 4)


def bfs_next_step(
    start: tuple[int, int],
    goal: tuple[int, int],
    wall_set: set[tuple[int, int]],
    width: int,
    height: int,
    occupied: set[tuple[int, int]] | None = None,
) -> tuple[tuple[int, int], int]:
    """
    BFS from start toward goal, avoiding walls (and optionally occupied cells).
    Returns (next_cell, distance).  If unreachable returns (start, 9999).
    """
    if start == goal:
        return start, 0
    from collections import deque
    blocked = wall_set | (occupied or set()) - {start, goal}
    queue = deque([(start, 0, None)])  # (pos, dist, first_step)
    visited = {start}
    while queue:
        pos, dist, first = queue.popleft()
        x, y = pos
        for nx, ny in [(x, y-1), (x, y+1), (x-1, y), (x+1, y)]:
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            npos = (nx, ny)
            if npos in visited or npos in blocked:
                continue
            visited.add(npos)
            step = first if first is not None else npos
            if npos == goal:
                return step, dist + 1
            queue.append((npos, dist + 1, step))
    return start, 9999


def best_approach(
    start: tuple[int, int],
    item_pos: tuple[int, int],
    wall_set: set[tuple[int, int]],
    width: int,
    height: int,
) -> tuple[tuple[int, int], int]:
    """
    Find the best walkable cell adjacent to item_pos and BFS to it.
    Items sit on walls — you approach an adjacent walkable cell to pick up.
    Returns (next_step, total_distance).
    """
    ix, iy = item_pos
    candidates = []
    for nx, ny in [(ix, iy-1), (ix, iy+1), (ix-1, iy), (ix+1, iy)]:
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in wall_set:
            nc, d = bfs_next_step(start, (nx, ny), wall_set, width, height)
            candidates.append((d, nc))
    if not candidates:
        return start, 9999
    candidates.sort()
    return candidates[0][1], candidates[0][0]


def precompute_item_approach(
    item_pos: tuple[int, int],
    wall_set: set[tuple[int, int]],
    width: int,
    height: int,
) -> dict[tuple[int, int], tuple[tuple[int, int], int]]:
    """
    Multi-source BFS from all walkable cells adjacent to item_pos.
    Returns {src_pos: (first_step_toward_item, distance)} for every reachable cell.
    Called once per item at episode start; lookups are then O(1).
    """
    from collections import deque

    ix, iy = item_pos
    sources: list[tuple[int, int]] = [
        (nx, ny)
        for nx, ny in [(ix, iy-1), (ix, iy+1), (ix-1, iy), (ix+1, iy)]
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in wall_set
    ]
    if not sources:
        return {}

    # BFS outward from approach cells. parent[pos] = one step closer to item.
    dist: dict[tuple, int] = {}
    parent: dict[tuple, tuple] = {}
    queue: deque = deque()
    for src in sources:
        dist[src] = 0
        parent[src] = src   # already adjacent — stay put, then pick_up
        queue.append(src)

    while queue:
        pos = queue.popleft()
        x, y = pos
        for nx, ny in [(x, y-1), (x, y+1), (x-1, y), (x+1, y)]:
            npos = (nx, ny)
            if npos in dist:
                continue
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if npos in wall_set:
                continue
            dist[npos] = dist[pos] + 1
            parent[npos] = pos
            queue.append(npos)

    # The first step from any pos toward the item is simply parent[pos].
    # parent[pos] points one cell closer to the approach cell.
    # Special case d==0: already adjacent, first_step = pos (issue pick_up, don't move).
    return {
        pos: (parent[pos], dist[pos])
        for pos in dist
    }


# ---------------------------------------------------------------------------
# Replay iterator
# ---------------------------------------------------------------------------

def iter_replays(replay_dir: str | Path) -> Iterator[list[dict]]:
    """
    Yield trajectories from recorded .json.gz replay files.
    Each trajectory is a list of dicts: {round, state, actions, reward}
    """
    replay_dir = Path(replay_dir)
    files = sorted(replay_dir.glob("*.json.gz"))
    if not files:
        raise FileNotFoundError(f"No replay files found in {replay_dir}")

    for fpath in files:
        with gzip.open(fpath, "rt", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "trajectory" in data:
            yield data["trajectory"]



# ---------------------------------------------------------------------------
# Formal MDP definition  (MARL book, Definition 1)
# ---------------------------------------------------------------------------

@dataclass
class MDPState:
    """
    Hashable snapshot of the full environment state at one timestep.

    Corresponds to s_t ∈ S in the MDP tuple (S, A, R, T, µ).
    The Markov property holds: T(s_{t+1} | s_t, a_t) is fully determined
    by this state — no history is needed.
    """
    round:            int
    bot_positions:    tuple[tuple[int, int], ...]    # one per bot
    bot_inventories:  tuple[tuple[str, ...], ...]    # one per bot
    items_on_shelf:   frozenset[tuple[str, str]]     # {(id, type), ...}
    active_needed:    tuple[str, ...]                # remaining items for active order
    preview_needed:   tuple[str, ...]                # items needed by preview order
    score:            int

    def __hash__(self):
        return hash((
            self.round, self.bot_positions, self.bot_inventories,
            self.items_on_shelf, self.active_needed, self.preview_needed,
            self.score,
        ))

    def __eq__(self, other):
        return (
            self.round == other.round
            and self.bot_positions == other.bot_positions
            and self.bot_inventories == other.bot_inventories
            and self.items_on_shelf == other.items_on_shelf
            and self.active_needed == other.active_needed
            and self.preview_needed == other.preview_needed
            and self.score == other.score
        )


@dataclass
class MDPTransition:
    """
    One step of the MDP: (s_t, a_t, r_t, s_{t+1}, terminal).

    Represents the tuple produced by T(s_t, a_t, s_{t+1}) and R(s_t, a_t, s_{t+1}).
    Because the simulator is deterministic given a seed, T(s_{t+1} | s_t, a_t) = 1
    for the observed next state and 0 for all others.
    """
    state:       MDPState
    actions:     tuple[int, ...]   # joint action a_t ∈ A^n
    reward:      float             # r_t = R(s_t, a_t, s_{t+1})
    next_state:  MDPState
    terminal:    bool              # s_{t+1} ∈ S̄  (terminal states)


class GroceryMDP:
    """
    Formal Markov Decision Process for the Grocery Bot challenge.

    Implements Definition 1 from the MARL book:
        MDP = (S, A, R, T, µ)

    Components
    ──────────
    S  — MDPState dataclass above; captures the full Markov state.
         |S| is exponential in bots × items × order combinations but the
         simulator samples trajectories rather than enumerating S.

    A  — Joint discrete action space: A = {0..6}^n_bots
         0=move_up  1=move_down  2=move_left  3=move_right
         4=pick_up  5=drop_off   6=wait
         |A| = 7^n_bots  (7 for easy, 343 for medium, 16807 for hard, …)

    R  — R(s, a, s') defined by step():
         +2×score_delta (needed pickup +1, order complete +5)
         +0.4 useful pickup (active order)
         +0.2 useful pickup (preview order)
         −0.5 duplicate pickup
         −0.3 useless pickup
         −0.02×n_idle per step

    T  — Deterministic given seed: T(s'|s,a) = 1 for the unique successor
         produced by _apply_action + _process_deliveries.

    µ  — Initial state distribution: uniform over seeds; a single seed
         produces a deterministic initial state s_0 = reset(seed).

    Usage
    ─────
    mdp = GroceryMDP(difficulty="easy", seed=42)
    s0  = mdp.initial_state()

    # Enumerate the 7 single-bot actions and their successors:
    for a in mdp.actions():
        s1, r, terminal = mdp.step(s0, [a])
        print(f"action={GroceryEnv.ACTION_NAMES[a]}  reward={r:.2f}  terminal={terminal}")

    # Roll out a full episode:
    trajectory = mdp.rollout(policy=lambda s, env: [random.randint(0,6)])
    returns = sum(t.reward for t in trajectory)
    """

    def __init__(
        self,
        difficulty: str = "easy",
        seed: int = 42,
        map_source: str = "hardcoded",
    ):
        self.difficulty = difficulty
        self.seed = seed
        self._env = GroceryEnv(
            difficulty=difficulty,
            seed=seed,
            map_source=map_source,
        )
        self._env.reset()

    # ── S: State space ───────────────────────────────────────────────────────

    def state_from_env(self) -> MDPState:
        """Extract the current MDP state s_t from the live simulator."""
        d = self._env.get_state_dict()
        active  = next((o for o in d["orders"] if o["status"] == "active"),  None)
        preview = next((o for o in d["orders"] if o["status"] == "preview"), None)
        return MDPState(
            round           = d["round"],
            bot_positions   = tuple(tuple(b["position"]) for b in d["bots"]),
            bot_inventories = tuple(tuple(b["inventory"]) for b in d["bots"]),
            items_on_shelf  = frozenset((i["id"], i["type"]) for i in d["items"]),
            active_needed   = tuple(_needed_types(active)),
            preview_needed  = tuple(_needed_types(preview)),
            score           = d["score"],
        )

    # ── A: Action space ──────────────────────────────────────────────────────

    def actions(self) -> list[int]:
        """
        A — individual action set for one agent.
        The joint action space is the Cartesian product A^n_bots.
        """
        return list(range(GroceryEnv.N_ACTIONS))   # [0, 1, 2, 3, 4, 5, 6]

    def joint_actions(self) -> list[tuple[int, ...]]:
        """
        Full joint action space A^n = A × A × … × A (|A|^n elements).
        Only feasible for easy (7^1=7) and medium (7^3=343).
        """
        from itertools import product
        n = self._env.n_bots
        return list(product(range(GroceryEnv.N_ACTIONS), repeat=n))

    @property
    def action_names(self) -> list[str]:
        return GroceryEnv.ACTION_NAMES

    # ── T + R: Transition and reward ─────────────────────────────────────────

    def step(
        self,
        state: MDPState,
        joint_action: list[int],
    ) -> tuple[MDPState, float, bool]:
        """
        Apply T and R: given (s_t, a_t) → (s_{t+1}, r_t, terminal).

        The simulator is deterministic conditioned on the seed, so
        T(s_{t+1} | s_t, a_t) = 1 for the returned next_state and 0 otherwise.

        Note: this advances the internal simulator state. Call reset() to
        restart from µ (the initial state distribution).
        """
        _, reward, terminal, _ = self._env.step(joint_action)
        next_state = self.state_from_env()
        return next_state, reward, terminal

    # ── µ: Initial state distribution ────────────────────────────────────────

    def initial_state(self, seed: int | None = None) -> MDPState:
        """
        Sample s_0 ~ µ.  With a fixed seed this is deterministic.
        Resets the internal simulator to the chosen seed.
        """
        if seed is not None:
            self._env.seed = seed
        self._env.reset()
        return self.state_from_env()

    def reset(self, seed: int | None = None) -> MDPState:
        """Alias for initial_state() — matches gym convention."""
        return self.initial_state(seed)

    # ── Full episode rollout ─────────────────────────────────────────────────

    def rollout(
        self,
        policy,            # callable(state, env) -> list[int]  joint action
        seed: int | None = None,
        max_steps: int = MAX_ROUNDS,
    ) -> list[MDPTransition]:
        """
        Roll out one episode under `policy`, collecting the trajectory
        τ = [(s_0, a_0, r_0, s_1), (s_1, a_1, r_1, s_2), …].

        Returns a list of MDPTransition objects.  The discounted return
        G_0 = Σ_{t=0}^{T} γ^t r_t can be computed as:

            G = sum(γ**t * tr.reward for t, tr in enumerate(trajectory))

        Example policies
        ────────────────
            # Random policy
            policy = lambda s, env: [random.randint(0, 6) for _ in range(env.n_bots)]

            # Greedy guided policy
            from marl_agent import guided_action
            policy = lambda s, env: [guided_action(i, env) for i in range(env.n_bots)]
        """
        s = self.initial_state(seed)
        trajectory: list[MDPTransition] = []
        for _ in range(max_steps):
            actions = policy(s, self._env)
            s_next, reward, terminal = self.step(s, actions)
            trajectory.append(MDPTransition(
                state=s, actions=tuple(actions),
                reward=reward, next_state=s_next, terminal=terminal,
            ))
            s = s_next
            if terminal:
                break
        return trajectory

    # ── Value function helpers ────────────────────────────────────────────────

    @staticmethod
    def discounted_return(trajectory: list[MDPTransition], gamma: float = 0.99) -> float:
        """
        G_0 = Σ_{t=0}^{T} γ^t r_t

        The return from the start of the episode under discount factor γ.
        γ=1 gives total undiscounted reward (= final score × scaling).
        """
        G = 0.0
        for t, tr in enumerate(trajectory):
            G += (gamma ** t) * tr.reward
        return G

    @staticmethod
    def monte_carlo_returns(
        trajectory: list[MDPTransition], gamma: float = 0.99
    ) -> list[float]:
        """
        Compute G_t = Σ_{k=0}^{T-t} γ^k r_{t+k} for every timestep t.

        Used in Monte Carlo policy evaluation: the return from each state
        s_t is an unbiased sample of V^π(s_t).
        """
        T = len(trajectory)
        returns = [0.0] * T
        G = 0.0
        for t in reversed(range(T)):
            G = trajectory[t].reward + gamma * G
            returns[t] = G
        return returns

    # ── MDP summary ──────────────────────────────────────────────────────────

    def describe(self) -> str:
        cfg = self._env.cfg
        n   = self._env.n_bots
        return (
            f"GroceryMDP — {self.difficulty.upper()}\n"
            f"  Grid:         {cfg['width']}×{cfg['height']}\n"
            f"  |S|:          exponential (bots={n}, items≤{cfg['width']*cfg['n_aisles']}, "
            f"item_types={len(ITEM_NAMES)})\n"
            f"  |A| per bot:  {GroceryEnv.N_ACTIONS}  "
            f"({', '.join(GroceryEnv.ACTION_NAMES)})\n"
            f"  |A| joint:    {GroceryEnv.N_ACTIONS}^{n} = "
            f"{GroceryEnv.N_ACTIONS**n}\n"
            f"  T:            deterministic (given seed={self.seed})\n"
            f"  R:            shaped delivery reward  "
            f"(+1/needed pickup, +5/order, pickup shaping)\n"
            f"  Horizon:      T = {MAX_ROUNDS} steps (episodic)\n"
            f"  µ:            deterministic initial state for fixed seed\n"
        )



if __name__ == "__main__":
    for diff in ["easy", "medium", "hard", "expert"]:
        env = GroceryEnv(difficulty=diff, seed=1337)
        obs = env.reset()
        total_r = 0.0
        done = False
        step = 0
        while not done:
            # Random policy for smoke test
            acts = [random.randint(0, GroceryEnv.N_ACTIONS - 1) for _ in range(env.n_bots)]
            obs, r, done, info = env.step(acts)
            total_r += r
            step += 1
        print(f"{diff:8s} | rounds={step} | score={info['score']} | total_reward={total_r:.1f}")
