#!/usr/bin/env python3
import argparse
import asyncio
import json
import math
import random
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

try:
    import websockets
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: websockets. Install with: pip install websockets") from exc

Pos = Tuple[int, int]

MOVE_DELTAS = {
    "move_up": (0, -1),
    "move_down": (0, 1),
    "move_left": (-1, 0),
    "move_right": (1, 0),
}
DELTA_TO_MOVE = {v: k for k, v in MOVE_DELTAS.items()}


@dataclass
class Task:
    kind: str
    target: Optional[Pos] = None
    item_id: Optional[str] = None
    shelf_pos: Optional[Pos] = None
    value: float = 0.0
    priority: int = 0


@dataclass
class Assignment:
    bot_id: int
    task: Task
    score: float


class WorldModel:
    def __init__(self, state: dict):
        grid = state["grid"]
        self.width = grid["width"]
        self.height = grid["height"]
        self.walls: Set[Pos] = {tuple(w) for w in grid["walls"]}
        self.drop_zones: List[Pos] = [tuple(z) for z in state.get("drop_off_zones") or [state["drop_off"]]]

        # Shelves are item cells and are not walkable.
        self.shelves: Set[Pos] = {tuple(item["position"]) for item in state["items"]}

        self.walkable: Set[Pos] = set()
        for y in range(self.height):
            for x in range(self.width):
                p = (x, y)
                if p in self.walls or p in self.shelves:
                    continue
                self.walkable.add(p)

        self.neighbors: Dict[Pos, List[Pos]] = {}
        for p in self.walkable:
            x, y = p
            outs = []
            for dx, dy in MOVE_DELTAS.values():
                n = (x + dx, y + dy)
                if n in self.walkable:
                    outs.append(n)
            self.neighbors[p] = outs
        self.degree: Dict[Pos, int] = {p: len(ns) for p, ns in self.neighbors.items()}
        self.corridor_cells: Set[Pos] = set()
        self.intersections: Set[Pos] = set()
        self.chokepoints: Set[Pos] = set()
        self.refuge_cells: List[Pos] = []
        self._compute_flow_topology()

        self.dist: Dict[Pos, Dict[Pos, int]] = {}
        self._compute_all_pairs_shortest_paths()

        self.pickup_adjacency: Dict[Pos, List[Pos]] = {}
        self._compute_pickup_adjacency()

        self.dist_to_drop: Dict[Pos, int] = {}
        self.nearest_drop: Dict[Pos, Pos] = {}
        self._compute_drop_zone_lookups()

    def _compute_all_pairs_shortest_paths(self) -> None:
        for src in self.walkable:
            q = deque([src])
            local = {src: 0}
            while q:
                cur = q.popleft()
                nd = local[cur] + 1
                for nxt in self.neighbors[cur]:
                    if nxt in local:
                        continue
                    local[nxt] = nd
                    q.append(nxt)
            self.dist[src] = local

    def _compute_pickup_adjacency(self) -> None:
        for shelf in self.shelves:
            x, y = shelf
            cells = []
            for dx, dy in MOVE_DELTAS.values():
                n = (x + dx, y + dy)
                if n in self.walkable:
                    cells.append(n)
            self.pickup_adjacency[shelf] = cells

    def _compute_drop_zone_lookups(self) -> None:
        for p in self.walkable:
            best_d = math.inf
            best_zone = self.drop_zones[0]
            dm = self.dist[p]
            for z in self.drop_zones:
                d = dm.get(z, math.inf)
                if d < best_d:
                    best_d = d
                    best_zone = z
            self.dist_to_drop[p] = int(best_d) if best_d < math.inf else 10**9
            self.nearest_drop[p] = best_zone

    def _compute_flow_topology(self) -> None:
        # Corridor: degree==2 and both neighbors are collinear (straight aisle lane).
        for p in self.walkable:
            deg = self.degree[p]
            ns = self.neighbors[p]
            if deg >= 3:
                self.intersections.add(p)
            if deg == 2:
                a, b = ns[0], ns[1]
                if a[0] == b[0] or a[1] == b[1]:
                    self.corridor_cells.add(p)
        self.chokepoints = self.intersections | self.corridor_cells

        # Refuge cells: low-choke, reasonably connected floor tiles for parking idle bots.
        candidates = []
        for p in self.walkable:
            if p in self.drop_zones:
                continue
            deg = self.degree[p]
            choke_pen = 1 if p in self.chokepoints else 0
            edge_bias = min(p[0], p[1], self.width - 1 - p[0], self.height - 1 - p[1])
            score = 2.0 * deg - 3.0 * choke_pen + 0.15 * edge_bias
            candidates.append((score, p))
        candidates.sort(key=lambda t: t[0], reverse=True)
        self.refuge_cells = [p for _, p in candidates[: max(12, min(40, len(candidates) // 6))]]

    def shortest(self, src: Pos, dst: Pos) -> int:
        return self.dist.get(src, {}).get(dst, 10**9)

    def min_dist_to_any(self, src: Pos, targets: List[Pos]) -> int:
        if src not in self.dist:
            return 10**9
        dm = self.dist[src]
        return min((dm.get(t, 10**9) for t in targets), default=10**9)


class HierarchicalController:
    def __init__(self, reservation_horizon: int = 8, decision_budget_ms: float = 450.0):
        self.world: Optional[WorldModel] = None
        self.reservation_horizon = reservation_horizon
        self.decision_budget_ms = max(50.0, min(580.0, decision_budget_ms))
        self.round_robin_offset = 0
        self.heat = defaultdict(float)
        self.prev_pos: Dict[int, Pos] = {}
        self.prev_prev_pos: Dict[int, Pos] = {}
        self.prev_step_pos: Dict[int, Optional[Pos]] = {}
        self.stuck_rounds: Dict[int, int] = defaultdict(int)
        self.osc_rounds: Dict[int, int] = defaultdict(int)
        self.intent_task: Dict[int, Task] = {}
        self.intent_age: Dict[int, int] = defaultdict(int)
        self.role_by_bot: Dict[int, str] = {}
        self.role_age: Dict[int, int] = defaultdict(int)
        self.prev_active_idx: Optional[int] = None
        self.active_stall_rounds: int = 0
        self.spawn_pos: Optional[Pos] = None
        self.spread_targets: List[Pos] = []

    @staticmethod
    def _task_key(task: Task) -> Tuple[str, Optional[Pos], Optional[str]]:
        return (task.kind, task.target, task.item_id)

    @staticmethod
    def _role_key(task: Task) -> str:
        if task.kind in ("drop_now", "deliver"):
            return "courier"
        if task.kind == "pickup_active":
            return "finisher"
        if task.kind == "pickup_preview":
            return "prefetcher"
        if task.kind == "clear_lane":
            return "yielder"
        return "repositioner"

    def _build_spread_targets(self) -> None:
        assert self.world is not None
        if self.spawn_pos is None:
            return
        scored: List[Tuple[float, Pos]] = []
        for p in self.world.walkable:
            if p in self.world.drop_zones:
                continue
            d_spawn = self.world.shortest(self.spawn_pos, p)
            if d_spawn >= 10**9:
                continue
            d_drop = self.world.dist_to_drop.get(p, 0)
            deg = self.world.degree.get(p, 0)
            choke_pen = 1.0 if p in self.world.chokepoints else 0.0
            score = 1.5 * d_spawn + 0.5 * d_drop + 0.8 * deg - 4.0 * choke_pen
            scored.append((score, p))
        scored.sort(key=lambda t: t[0], reverse=True)
        self.spread_targets = [p for _, p in scored[:120]]

    def _committed_carried_active(
        self,
        bots: List[dict],
        active_need: Counter,
        eta_threshold: int,
    ) -> Counter:
        """
        Count active-needed inventory that is likely to convert soon.
        Items carried far from drop-off are not treated as fully committed,
        which allows backup pickups instead of stalling completion.
        """
        assert self.world is not None
        by_type_etas: Dict[str, List[int]] = defaultdict(list)
        for b in bots:
            pos = tuple(b["position"])
            to_drop = self.world.dist_to_drop.get(pos, 10**9)
            invc = Counter(b["inventory"])
            for typ, need in active_need.items():
                if need <= 0:
                    continue
                cnt = invc.get(typ, 0)
                if cnt <= 0:
                    continue
                by_type_etas[typ].extend([to_drop] * cnt)

        committed = Counter()
        for typ, need in active_need.items():
            etas = sorted(by_type_etas.get(typ, []))
            take = 0
            for e in etas:
                if take >= need:
                    break
                if e <= eta_threshold:
                    take += 1
            committed[typ] = take
        return committed

    def _estimate_active_completion_eta(
        self,
        bots: List[dict],
        items_by_type: Dict[str, List[dict]],
        active_need: Counter,
    ) -> int:
        """
        Estimate rounds to complete the active order using true unmet needs.
        For each required type with multiplicity n, take the n-th best ETA candidate
        from carried items (to drop) and shelf pickups (pickup+drop).
        """
        assert self.world is not None
        type_eta: Dict[str, int] = {}
        for typ, need in active_need.items():
            if need <= 0:
                continue
            candidates: List[int] = []

            # Carried copies: ETA is distance to any drop.
            for b in bots:
                invc = Counter(b["inventory"])
                cnt = invc.get(typ, 0)
                if cnt <= 0:
                    continue
                pos_b = tuple(b["position"])
                d_drop = self.world.dist_to_drop.get(pos_b, 10**9)
                candidates.extend([d_drop] * cnt)

            # Shelf copies: ETA is best bot-to-pickup-adjacent + pickup-adjacent-to-drop.
            for it in items_by_type.get(typ, []):
                shelf = tuple(it["position"])
                adj = self.world.pickup_adjacency.get(shelf, [])
                if not adj:
                    continue
                to_pick = min((self.world.min_dist_to_any(tuple(b["position"]), adj) for b in bots), default=10**9)
                pick_to_drop = min((self.world.dist_to_drop.get(c, 10**9) for c in adj), default=10**9)
                candidates.append(to_pick + pick_to_drop)

            candidates.sort()
            if len(candidates) >= need:
                type_eta[typ] = candidates[need - 1]
            elif candidates:
                type_eta[typ] = 10**9
            else:
                type_eta[typ] = 10**9

        return max(type_eta.values(), default=0)

    def _ensure_world(self, state: dict) -> None:
        if self.world is None:
            self.world = WorldModel(state)

    def _decay_and_update_heat(self, bots: List[dict]) -> None:
        for k in list(self.heat.keys()):
            self.heat[k] *= 0.88
            if self.heat[k] < 0.05:
                del self.heat[k]
        for b in bots:
            self.heat[tuple(b["position"])] += 1.0

    def _update_stuck_tracking(self, bots: List[dict]) -> None:
        for b in bots:
            bid = b["id"]
            pos = tuple(b["position"])
            prev = self.prev_pos.get(bid)
            prev2 = self.prev_prev_pos.get(bid)
            self.prev_step_pos[bid] = prev

            if prev is not None and prev == pos:
                self.stuck_rounds[bid] += 1
            else:
                self.stuck_rounds[bid] = 0

            # A-B-A oscillation signal.
            if prev is not None and prev2 is not None and pos == prev2 and pos != prev:
                self.osc_rounds[bid] += 1
            else:
                self.osc_rounds[bid] = max(0, self.osc_rounds[bid] - 1)

            self.prev_prev_pos[bid] = prev if prev is not None else pos
            self.prev_pos[bid] = pos

    @staticmethod
    def _order_need(order: Optional[dict]) -> Counter:
        if not order:
            return Counter()
        req = Counter(order["items_required"])
        delivered = Counter(order["items_delivered"])
        out = req - delivered
        for k in list(out.keys()):
            if out[k] <= 0:
                del out[k]
        return out

    @staticmethod
    def _active_preview(orders: List[dict]) -> Tuple[Optional[dict], Optional[dict]]:
        active = None
        preview = None
        for o in orders:
            if o.get("status") == "active":
                active = o
            elif o.get("status") == "preview":
                preview = o
        return active, preview

    def _best_pickup_cell(self, bot_pos: Pos, shelf_pos: Pos) -> Tuple[Pos, int]:
        assert self.world is not None
        candidates = self.world.pickup_adjacency.get(shelf_pos, [])
        best = None
        best_d = 10**9
        for c in candidates:
            d = self.world.shortest(bot_pos, c)
            if d < best_d:
                best_d = d
                best = c
        return (best if best is not None else bot_pos, best_d)

    def _estimate_active_pressure(self, bots: List[dict], active_need: Counter, items_by_type: Dict[str, List[dict]]) -> float:
        assert self.world is not None
        if not active_need:
            return 0.0
        needed = sum(active_need.values())
        est_pick = 0
        for item_type, cnt in active_need.items():
            shelves = items_by_type.get(item_type, [])
            if not shelves:
                est_pick += cnt * 12
                continue
            sample = shelves[: min(6, len(shelves))]
            best = 10**9
            for bot in bots:
                p = tuple(bot["position"])
                for s in sample:
                    _, d = self._best_pickup_cell(p, tuple(s["position"]))
                    best = min(best, d)
            est_pick += best * cnt
        return est_pick / max(1, needed)

    def _role_budgets(self, bots: List[dict], active_need: Counter, preview_need: Counter, items_by_type: Dict[str, List[dict]]) -> dict:
        pressure = self._estimate_active_pressure(bots, active_need, items_by_type)
        n = len(bots)
        if not preview_need:
            return {"active": n, "preview": 0}
        if pressure <= 5:
            preview = min(max(2, n // 4), n // 2)
        elif pressure <= 8:
            preview = min(max(1, n // 6), n // 3)
        else:
            preview = 0
        return {"active": n - preview, "preview": preview}

    def _task_value(
        self,
        task_kind: str,
        carrying_active: int,
        scarce_bonus: float,
        near_completion: bool,
        preview_bias: float,
    ) -> float:
        if task_kind == "drop_now":
            return 200 + 15 * carrying_active
        if task_kind == "deliver":
            base = 130 + 12 * carrying_active
            if near_completion:
                base += 30
            return base
        if task_kind == "pickup_active":
            base = 85 + 8 * scarce_bonus
            if near_completion:
                base += 15
            return base
        if task_kind == "pickup_preview":
            return 45 + 10 * preview_bias
        if task_kind == "staging":
            return 18
        if task_kind == "clear_lane":
            return 28
        return 0

    def _best_refuge(self, pos: Pos, reserved_targets: Set[Pos]) -> Optional[Pos]:
        assert self.world is not None
        best = None
        best_key = (10**9, 10**9)
        for r in self.world.refuge_cells:
            if r in reserved_targets:
                continue
            d = self.world.shortest(pos, r)
            if d >= 10**9:
                continue
            key = (d, self.heat.get(r, 0.0))
            if key < best_key:
                best_key = key
                best = r
        return best

    def _make_candidates(self, state: dict) -> Dict[int, List[Task]]:
        assert self.world is not None
        bots = state["bots"]
        items = state["items"]
        round_no = int(state.get("round", 0))
        active_idx = int(state.get("active_order_index", 0))
        rounds_left = max(0, int(state.get("max_rounds", 300)) - int(state.get("round", 0)))
        stall_rounds = int(state.get("_active_stall_rounds", 0))
        if rounds_left <= 20:
            endgame_phase = "sprint"
        elif rounds_left <= 100:
            endgame_phase = "focus"
        else:
            endgame_phase = "normal"
        active_order, preview_order = self._active_preview(state["orders"])
        active_need = self._order_need(active_order)
        preview_need = self._order_need(preview_order)
        active_need_total = sum(active_need.values())
        unstick_mode = stall_rounds >= 30 and active_need_total > 0

        commit_eta = 12 if endgame_phase == "normal" else (9 if endgame_phase == "focus" else 7)
        if stall_rounds >= 20 and active_need_total <= 2:
            # During prolonged near-finish stalls, do not assume far-carried items are "covered".
            commit_eta = 2
        carried_active = self._committed_carried_active(bots, active_need, eta_threshold=commit_eta)
        carried_preview = Counter()
        for b in bots:
            inv = b["inventory"]
            for it in inv:
                if preview_need[it] > 0:
                    carried_preview[it] += 1

        remaining_active = active_need - carried_active
        remaining_preview = preview_need - carried_preview

        scarcity = {}
        items_by_type: Dict[str, List[dict]] = defaultdict(list)
        for item in items:
            items_by_type[item["type"]].append(item)
        for typ, need in remaining_active.items():
            supply = len(items_by_type.get(typ, []))
            scarcity[typ] = need / max(1, supply)
        active_completion_eta = self._estimate_active_completion_eta(bots, items_by_type, active_need)
        if stall_rounds >= 20 and active_need_total > 0:
            # ETA can be over-optimistic during jams; keep planner in active-first mode.
            active_completion_eta = max(active_completion_eta, 6)
        # Remaining-active bottlenecks for pickup prioritization.
        type_best_eta: Dict[str, int] = {}
        for typ, need in remaining_active.items():
            if need <= 0:
                continue
            best = 10**9
            for b in bots:
                pos_b = tuple(b["position"])
                invc = Counter(b["inventory"])
                if invc.get(typ, 0) > 0:
                    best = min(best, self.world.dist_to_drop.get(pos_b, 10**9))
            for shelf_item in items_by_type.get(typ, []):
                shelf = tuple(shelf_item["position"])
                adj_cells = self.world.pickup_adjacency.get(shelf, [])
                if not adj_cells:
                    continue
                pickup_to_drop = min((self.world.dist_to_drop.get(c, 10**9) for c in adj_cells), default=10**9)
                for b in bots:
                    pos_b = tuple(b["position"])
                    to_pick = self.world.min_dist_to_any(pos_b, adj_cells)
                    best = min(best, to_pick + pickup_to_drop)
            type_best_eta[typ] = best
        bottleneck_types: Set[str] = {
            t for t, e in type_best_eta.items() if e >= max(6, active_completion_eta - 2)
        }
        state["_active_eta_est"] = active_completion_eta

        role_budgets = self._role_budgets(bots, remaining_active, remaining_preview, items_by_type)
        near_completion = sum(remaining_active.values()) <= 2
        # Explicit order-centric dynamic roles.
        n_bots = len(bots)
        if active_completion_eta >= 14:
            finisher_budget = max(16, (4 * n_bots) // 5)
            prefetch_budget = 0
            yielder_budget = max(1, n_bots // 10)
        elif active_completion_eta >= 9:
            finisher_budget = max(14, (7 * n_bots) // 10)
            prefetch_budget = min(2, n_bots // 8)
            yielder_budget = max(1, n_bots // 12)
        elif active_completion_eta >= 5:
            finisher_budget = max(12, (3 * n_bots) // 5)
            prefetch_budget = min(4, n_bots // 5)
            yielder_budget = max(1, n_bots // 12)
        else:
            finisher_budget = max(10, n_bots // 2)
            prefetch_budget = min(6, n_bots // 4)
            yielder_budget = max(1, n_bots // 14)

        # Recovery mode: if active order has stalled for too long, suppress side objectives.
        recovery_mode = stall_rounds >= 24 and active_completion_eta >= 10
        critical_finish_mode = (
            stall_rounds >= 40
            and active_need_total == 1
            and active_completion_eta >= 4
        )
        if recovery_mode:
            finisher_budget = n_bots
            prefetch_budget = 0
            yielder_budget = 0
        if critical_finish_mode:
            finisher_budget = min(n_bots, max(6, active_need_total * 6))
            prefetch_budget = 0
            yielder_budget = max(yielder_budget, max(2, n_bots // 8))
        # In late game, reduce swarm pressure: fewer bots should actively pursue pickup tasks.
        if endgame_phase == "focus":
            role_budgets["active"] = min(role_budgets["active"], max(15, (3 * len(bots)) // 4))
            role_budgets["preview"] = min(role_budgets["preview"], max(0, len(bots) // 8))
            prefetch_budget = min(prefetch_budget, 2)
        elif endgame_phase == "sprint":
            role_budgets["active"] = min(role_budgets["active"], max(18, (9 * len(bots)) // 10))
            role_budgets["preview"] = 0
            prefetch_budget = 0
        if recovery_mode:
            role_budgets["active"] = n_bots
            role_budgets["preview"] = 0
        if critical_finish_mode:
            role_budgets["active"] = min(role_budgets["active"], finisher_budget)
            role_budgets["preview"] = 0
        if unstick_mode:
            role_budgets["active"] = n_bots
            role_budgets["preview"] = 0
            prefetch_budget = 0
            yielder_budget = min(yielder_budget, 1)
        state["_critical_finish_mode"] = critical_finish_mode
        state["_unstick_mode"] = unstick_mode
        opening_spread_mode = round_no <= 45 and active_idx <= 1 and self.spawn_pos is not None and bool(self.spread_targets)
        state["_opening_spread_mode"] = opening_spread_mode

        # Assign nearest "hunters" for each missing active type to reduce task dilution.
        hunter_types_by_bot: Dict[int, Set[str]] = defaultdict(set)
        for typ, need in remaining_active.items():
            if need <= 0:
                continue
            shelves = items_by_type.get(typ, [])
            if not shelves:
                continue
            ranked: List[Tuple[int, int]] = []
            for b in bots:
                bid = b["id"]
                p = tuple(b["position"])
                best = 10**9
                for it in shelves:
                    shelf = tuple(it["position"])
                    d = self.world.min_dist_to_any(p, self.world.pickup_adjacency.get(shelf, []))
                    if d < best:
                        best = d
                ranked.append((best, bid))
            ranked.sort(key=lambda t: t[0])
            k = min(len(ranked), max(2, 2 * need))
            for _, bid in ranked[:k]:
                hunter_types_by_bot[bid].add(typ)

        candidates: Dict[int, List[Task]] = {}
        refuge_claims: Set[Pos] = set()
        active_chasers = 0
        preview_chasers = 0
        yielding_assigned = 0
        spread_assigned = 0
        spread_budget = max(0, len(bots) // 2) if opening_spread_mode else 0
        for b in bots:
            bot_id = b["id"]
            pos = tuple(b["position"])
            inv = b["inventory"]
            inv_counter = Counter(inv)
            room = 3 - len(inv)
            deliverable_now = sum(min(inv_counter[t], active_need[t]) for t in active_need)
            stale_items = sum(
                cnt for typ, cnt in inv_counter.items() if active_need[typ] <= 0 and preview_need[typ] <= 0
            )
            stuck = self.stuck_rounds.get(bot_id, 0)
            oscillating = self.osc_rounds.get(bot_id, 0)
            in_choke = pos in self.world.chokepoints

            local: List[Task] = []
            on_drop = pos in self.world.drop_zones
            if on_drop and deliverable_now > 0:
                local.append(Task(kind="drop_now", target=pos, value=self._task_value("drop_now", deliverable_now, 0, near_completion, 0), priority=0))
            elif deliverable_now > 0:
                # Dynamic drop zone choice includes congestion estimate.
                best_zone = None
                best_cost = 10**9
                for z in self.world.drop_zones:
                    d = self.world.shortest(pos, z)
                    cost = d + 0.8 * self.heat.get(z, 0.0)
                    if cost < best_cost:
                        best_cost = cost
                        best_zone = z
                deliver_value = self._task_value("deliver", deliverable_now, 0, near_completion, 0)
                # If active ETA is high, accelerate courier behavior.
                deliver_value += 0.8 * min(20, active_completion_eta)
                local.append(Task(kind="deliver", target=best_zone, value=deliver_value, priority=1))

            # Early-game decongestion: spread a subset of bots away from spawn/drop lanes.
            if (
                opening_spread_mode
                and spread_assigned < spread_budget
                and len(inv) == 0
                and deliverable_now == 0
                and self.spawn_pos is not None
                and self.world.shortest(self.spawn_pos, pos) <= 7
            ):
                target = self.spread_targets[(bot_id + round_no) % len(self.spread_targets)]
                spread_assigned += 1
                local.append(Task(kind="staging", target=target, value=88.0, priority=2))

            # Lane-clearing behavior: stuck/idle bots in choke cells relocate to refuge tiles.
            if (not recovery_mode) and in_choke and (stuck >= 4 or oscillating >= 3) and deliverable_now == 0 and yielding_assigned < yielder_budget:
                refuge = self._best_refuge(pos, refuge_claims)
                if refuge is not None and refuge != pos:
                    refuge_claims.add(refuge)
                    yielding_assigned += 1
                    local.append(
                        Task(
                            kind="clear_lane",
                            target=refuge,
                            value=self._task_value("clear_lane", 0, 0, near_completion, 0) + 8 * min(max(stuck, oscillating), 5),
                            priority=3,
                        )
                    )

            # Active pickups (adjacent-tile distance, not shelf distance)
            allow_active_pickups = room > 0 and (active_chasers < role_budgets["active"] or deliverable_now > 0)
            if allow_active_pickups:
                for typ, need in remaining_active.items():
                    if need <= 0:
                        continue
                    if (not critical_finish_mode) and (not unstick_mode) and hunter_types_by_bot.get(bot_id) and typ not in hunter_types_by_bot[bot_id]:
                        continue
                    # Carry no more than needed amount for active.
                    if inv_counter[typ] >= active_need[typ]:
                        continue
                    supplies = items_by_type.get(typ, [])
                    if not supplies:
                        continue
                    ranked = []
                    for item in supplies:
                        shelf = tuple(item["position"])
                        pickup_cell, d = self._best_pickup_cell(pos, shelf)
                        if d >= 10**9:
                            continue
                        eta_after_pick = d + self.world.dist_to_drop.get(pickup_cell, 10**9)
                        eta_gain = max(0, type_best_eta.get(typ, 10**9) - eta_after_pick)
                        ranked.append((d - 0.35 * eta_gain, item, pickup_cell, shelf, eta_gain))
                    ranked.sort(key=lambda x: x[0])
                    for _, item, pickup_cell, shelf, eta_gain in ranked[:2]:
                        value = self._task_value("pickup_active", 0, scarcity.get(typ, 0), near_completion, 0)
                        value += 2.2 * min(8, eta_gain)
                        if typ in bottleneck_types:
                            value += 18
                        if unstick_mode:
                            value += 25
                        local.append(
                            Task(
                                kind="pickup_active",
                                target=pickup_cell,
                                item_id=item["id"],
                                shelf_pos=shelf,
                                value=value,
                                priority=2,
                            )
                        )
                if any(t.kind == "pickup_active" for t in local):
                    active_chasers += 1

            # Preview pickups only for excess capacity roles.
            allow_preview = (
                room > 0
                and role_budgets["preview"] > 0
                and preview_chasers < prefetch_budget
                and endgame_phase in ("normal", "focus")
                and rounds_left > 260
                and active_need_total <= 2
                and active_completion_eta <= 3
                and stall_rounds < 12
                and deliverable_now == 0
                and stale_items == 0
                and len(inv) == 0
            )
            if allow_preview:
                preview_bias = 1.0 if sum(remaining_active.values()) <= len(bots) // 3 else 0.0
                for typ, need in remaining_preview.items():
                    if need <= 0:
                        continue
                    if inv_counter[typ] >= preview_need[typ]:
                        continue
                    supplies = items_by_type.get(typ, [])
                    ranked = []
                    for item in supplies:
                        shelf = tuple(item["position"])
                        pickup_cell, d = self._best_pickup_cell(pos, shelf)
                        if d >= 10**9:
                            continue
                        far_from_drop = self.world.dist_to_drop.get(pickup_cell, 0)
                        ranked.append((d - 0.2 * far_from_drop, item, pickup_cell, shelf))
                    ranked.sort(key=lambda x: x[0])
                    for _, item, pickup_cell, shelf in ranked[:1]:
                        local.append(
                            Task(
                                kind="pickup_preview",
                                target=pickup_cell,
                                item_id=item["id"],
                                shelf_pos=shelf,
                                value=self._task_value("pickup_preview", 0, 0, near_completion, preview_bias),
                                priority=3,
                            )
                        )
                if any(t.kind == "pickup_preview" for t in local):
                    preview_chasers += 1

            # Endgame parking: extra bots should avoid injecting noise into aisles.
            if not local and (endgame_phase == "focus" or critical_finish_mode) and not recovery_mode:
                refuge = self._best_refuge(pos, refuge_claims)
                if refuge is not None and refuge != pos:
                    refuge_claims.add(refuge)
                    local.append(Task(kind="clear_lane", target=refuge, value=34, priority=3))

            if not local and critical_finish_mode and not in_choke:
                local.append(Task(kind="wait", target=pos, value=20, priority=3))

            # Staging: move out of hot tiles/chokepoints when idle.
            if not local:
                best = pos
                best_score = -10**9
                for c in self.world.neighbors.get(pos, []) + [pos]:
                    clearance = len(self.world.neighbors.get(c, []))
                    heat_pen = self.heat.get(c, 0.0)
                    drop_d = self.world.dist_to_drop.get(c, 8)
                    choke_pen = 2.8 if c in self.world.chokepoints else 0.0
                    endgame_wander_pen = 0.6 if endgame_phase == "focus" and c != pos else 0.0
                    score = 0.7 * clearance - 1.2 * heat_pen - 0.05 * drop_d - choke_pen - endgame_wander_pen
                    if score > best_score:
                        best_score = score
                        best = c
                local.append(Task(kind="staging", target=best, value=self._task_value("staging", 0, 0, False, 0), priority=4))

            # Always keep an explicit wait fallback.
            local.append(Task(kind="wait", target=pos, value=0.0, priority=5))
            candidates[bot_id] = local

        return candidates

    def _score_pair(self, bot: dict, task: Task, target_counts: Dict[Pos, int], item_claims: Dict[str, int]) -> float:
        assert self.world is not None
        pos = tuple(bot["position"])

        if task.kind == "wait":
            return -5.0

        travel = self.world.shortest(pos, task.target) if task.target else 0
        congestion = self.heat.get(task.target, 0.0) if task.target else 0.0
        conflict = 0.0
        if task.target is not None:
            conflict += 8.0 * target_counts[task.target]
        if task.item_id:
            conflict += 40.0 * item_claims[task.item_id]
        if task.target is not None and task.target in self.world.chokepoints and task.kind in ("staging", "wait", "clear_lane"):
            conflict += 6.0
        if self.spawn_pos is not None and task.target is not None:
            # Early rounds: discourage sending idle traffic back toward spawn/drop crowd.
            if self.active_stall_rounds < 12 and self.world.shortest(self.spawn_pos, task.target) <= 5 and task.kind in ("staging", "wait"):
                conflict += 10.0
        # Avoid assigning non-wait tasks that don't move the bot.
        if task.target is not None and task.target == pos and task.kind not in ("drop_now", "wait"):
            conflict += 10.0

        return task.value - 1.9 * travel - 1.7 * congestion - conflict

    def _assign_tasks(
        self,
        state: dict,
        candidates: Dict[int, List[Task]],
        jitter: float = 0.0,
        shuffle_order: bool = False,
    ) -> Dict[int, Task]:
        bots = {b["id"]: b for b in state["bots"]}
        target_counts: Dict[Pos, int] = defaultdict(int)
        item_claims: Dict[str, int] = defaultdict(int)
        assigned: Dict[int, Task] = {}
        # First, urgency-based bot ordering (deliverers first).
        bot_order = sorted(
            bots.keys(),
            key=lambda bid: min((t.priority for t in candidates.get(bid, [])), default=9),
        )
        if shuffle_order:
            random.shuffle(bot_order)

        # Greedy assignment with dynamic penalties to spread bots.
        for bid in bot_order:
            bot = bots[bid]
            best_task = None
            best_score = -10**12
            prev_task = self.intent_task.get(bid)
            prev_key = self._task_key(prev_task) if prev_task is not None else None
            prev_age = self.intent_age.get(bid, 0)
            for task in candidates.get(bid, []):
                if task.item_id and item_claims[task.item_id] > 0:
                    continue
                score = self._score_pair(bot, task, target_counts, item_claims)
                if prev_key is not None and self._task_key(task) == prev_key and prev_age < 4:
                    score += 14.0 - 2.0 * prev_age
                if jitter > 0.0:
                    score += random.uniform(-jitter, jitter)
                if score > best_score:
                    best_score = score
                    best_task = task

            if best_task is None:
                best_task = Task(kind="wait", target=tuple(bot["position"]))
            assigned[bid] = best_task
            if best_task.target is not None:
                target_counts[best_task.target] += 1
            if best_task.item_id:
                item_claims[best_task.item_id] += 1

        # Ensure every bot gets something.
        for bot_id in bots:
            if bot_id not in assigned:
                assigned[bot_id] = Task(kind="wait", target=tuple(bots[bot_id]["position"]))

        # Update short-lived intents to reduce retarget thrash.
        next_intent_task: Dict[int, Task] = {}
        next_intent_age: Dict[int, int] = defaultdict(int)
        next_role_by_bot: Dict[int, str] = {}
        next_role_age: Dict[int, int] = defaultdict(int)
        for bid, task in assigned.items():
            prev_task = self.intent_task.get(bid)
            if prev_task is not None and self._task_key(prev_task) == self._task_key(task):
                next_intent_age[bid] = self.intent_age.get(bid, 0) + 1
            else:
                next_intent_age[bid] = 0
            next_intent_task[bid] = task
            new_role = self._role_key(task)
            old_role = self.role_by_bot.get(bid)
            if old_role == new_role:
                next_role_age[bid] = self.role_age.get(bid, 0) + 1
            else:
                next_role_age[bid] = 0
            next_role_by_bot[bid] = new_role
        self.intent_task = next_intent_task
        self.intent_age = next_intent_age
        self.role_by_bot = next_role_by_bot
        self.role_age = next_role_age

        return assigned

    def _adjacent(self, a: Pos, b: Pos) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def _plan_path_with_reservations(
        self,
        start: Pos,
        goals: Set[Pos],
        blocked: Dict[int, Set[Pos]],
        edge_blocked: Set[Tuple[Pos, Pos, int]],
    ) -> List[Pos]:
        assert self.world is not None

        horizon = self.reservation_horizon
        q = deque([(start, 0)])
        parent: Dict[Tuple[Pos, int], Tuple[Pos, int]] = {}
        seen = {(start, 0)}

        best_goal_node = None
        best_partial_node = (start, 0)
        best_partial_key = (10**9, 0.0)
        while q:
            pos, t = q.popleft()
            # Track best progress node even if no full goal is reached inside horizon.
            rem = min((self.world.shortest(pos, g) for g in goals), default=10**9)
            # Prefer smaller remaining distance, then lower heat, then larger t (more progress this round).
            key = (rem, self.heat.get(pos, 0.0) - 0.01 * t)
            if key < best_partial_key:
                best_partial_key = key
                best_partial_node = (pos, t)

            if pos in goals:
                best_goal_node = (pos, t)
                break
            if t >= horizon:
                continue
            options = list(self.world.neighbors.get(pos, [])) + [pos]
            for nxt in options:
                nt = t + 1
                if nxt in blocked.get(nt, set()):
                    continue
                if (pos, nxt, nt) in edge_blocked:
                    continue
                node = (nxt, nt)
                if node in seen:
                    continue
                seen.add(node)
                parent[node] = (pos, t)
                q.append(node)

        chosen = best_goal_node if best_goal_node is not None else best_partial_node

        # Reconstruct position sequence from time 0..t.
        seq = []
        node = chosen
        while True:
            seq.append(node[0])
            if node == (start, 0):
                break
            node = parent[node]
        seq.reverse()
        return seq

    def _reserve_path(
        self,
        path: List[Pos],
        blocked: Dict[int, Set[Pos]],
        edge_blocked: Set[Tuple[Pos, Pos, int]],
    ) -> None:
        last = path[0]
        max_t = max(1, self.reservation_horizon)
        for t in range(1, max_t + 1):
            cur = path[t] if t < len(path) else path[-1]
            blocked[t].add(cur)
            edge_blocked.add((last, cur, t))
            edge_blocked.add((cur, last, t))
            last = cur

    def _move_action(self, src: Pos, dst: Pos) -> str:
        if src == dst:
            return "wait"
        dx = dst[0] - src[0]
        dy = dst[1] - src[1]
        return DELTA_TO_MOVE.get((dx, dy), "wait")

    def _actions_from_assignments(
        self,
        state: dict,
        assigned: Dict[int, Task],
        planning_offset: Optional[int] = None,
        advance_round_robin: bool = False,
    ) -> List[dict]:
        assert self.world is not None

        bots = sorted(state["bots"], key=lambda b: b["id"])
        bot_by_id = {b["id"]: b for b in bots}
        items = state["items"]
        active_order, _ = self._active_preview(state["orders"])
        active_need = self._order_need(active_order)
        phase = state.get("_endgame_phase", "normal")
        stall_rounds = int(state.get("_active_stall_rounds", 0))
        recovery_mode = stall_rounds >= 24 and int(state.get("_active_eta_est", 0)) >= 10
        critical_finish_mode = bool(state.get("_critical_finish_mode", False))
        unstick_mode = bool(state.get("_unstick_mode", False))
        active_need_total = sum(active_need.values())
        commit_eta = 12 if phase == "normal" else (9 if phase == "focus" else 7)
        if stall_rounds >= 20 and active_need_total <= 2:
            commit_eta = 2
        carried_active = self._committed_carried_active(bots, active_need, eta_threshold=commit_eta)
        remaining_active = active_need - carried_active
        item_by_id = {it["id"]: it for it in items}
        items_at_pos: Dict[Pos, List[dict]] = defaultdict(list)
        for it in items:
            items_at_pos[tuple(it["position"])].append(it)
        claimed_item_ids: Set[str] = set()

        # Priority rotation to reduce starvation.
        ids = [b["id"] for b in bots]
        if ids:
            base_off = self.round_robin_offset if planning_offset is None else planning_offset
            k = base_off % len(ids)
            ordered_ids = ids[k:] + ids[:k]
        else:
            ordered_ids = []

        # Task urgency influences planning order.
        urgency = {
            "drop_now": 0,
            "deliver": 1,
            "pickup_active": 2,
            "clear_lane": 3,
            "pickup_preview": 3,
            "staging": 4,
            "wait": 5,
        }
        base_rank = {bid: i for i, bid in enumerate(ordered_ids)}
        ordered_ids.sort(key=lambda bid: (urgency.get(assigned[bid].kind, 9), base_rank[bid]))

        blocked: Dict[int, Set[Pos]] = defaultdict(set)
        edge_blocked: Set[Tuple[Pos, Pos, int]] = set()
        action_by_bot: Dict[int, dict] = {}
        nonproductive_moves = 0
        nonproductive_move_budget = 6 if unstick_mode else 999

        item_positions = {item["id"]: tuple(item["position"]) for item in state["items"]}

        for bid in ordered_ids:
            bot = bot_by_id[bid]
            pos = tuple(bot["position"])
            prev_pos = self.prev_step_pos.get(bid)
            osc = self.osc_rounds.get(bid, 0)
            task = assigned[bid]
            inv = bot["inventory"]
            inv_counter = Counter(inv)
            carrying_active_now = sum(min(inv_counter[t], active_need[t]) for t in active_need)

            # Hard courier override: if carrying active items, always head to drop until delivered.
            if carrying_active_now > 0:
                if pos in self.world.drop_zones:
                    action_by_bot[bid] = {"bot": bid, "action": "drop_off"}
                    self._reserve_path([pos, pos], blocked, edge_blocked)
                    continue
                best_zone = None
                best_key = (10**9, 10**9)
                for z in self.world.drop_zones:
                    d = self.world.shortest(pos, z)
                    key = (d, self.heat.get(z, 0.0))
                    if key < best_key:
                        best_key = key
                        best_zone = z
                if best_zone is not None:
                    task = Task(kind="deliver", target=best_zone, priority=0, value=999.0)

            if task.kind in ("drop_now", "deliver") and pos in self.world.drop_zones and inv:
                action_by_bot[bid] = {"bot": bid, "action": "drop_off"}
                self._reserve_path([pos, pos], blocked, edge_blocked)
                continue

            # Opportunistic active pickup: if already adjacent to needed item, pick it now.
            if len(inv) < 3:
                picked = None
                for npos in self.world.neighbors.get(pos, []):
                    for item in items_at_pos.get(npos, []):
                        iid = item["id"]
                        typ = item["type"]
                        if iid in claimed_item_ids:
                            continue
                        if remaining_active.get(typ, 0) <= 0:
                            continue
                        picked = iid
                        remaining_active[typ] -= 1
                        claimed_item_ids.add(iid)
                        break
                    if picked is not None:
                        break
                if picked is not None:
                    action_by_bot[bid] = {"bot": bid, "action": "pick_up", "item_id": picked}
                    self._reserve_path([pos, pos], blocked, edge_blocked)
                    continue

            if task.kind in ("pickup_active", "pickup_preview") and task.item_id in item_positions and len(inv) < 3:
                shelf = item_positions[task.item_id]
                if self._adjacent(pos, shelf):
                    action_by_bot[bid] = {"bot": bid, "action": "pick_up", "item_id": task.item_id}
                    claimed_item_ids.add(task.item_id)
                    it = item_by_id.get(task.item_id)
                    if it is not None and remaining_active.get(it["type"], 0) > 0:
                        remaining_active[it["type"]] -= 1
                    self._reserve_path([pos, pos], blocked, edge_blocked)
                    continue

            goals = {task.target} if task.target else {pos}
            path = self._plan_path_with_reservations(pos, goals, blocked, edge_blocked)
            nxt = path[1] if len(path) > 1 else pos

            # Anti-stall fallback: if we are still waiting on a non-wait task, try a legal 1-step descent.
            if nxt == pos and task.kind != "wait" and task.target is not None:
                best_alt = pos
                best_key = (10**9, 10**9)
                for cand in self.world.neighbors.get(pos, []):
                    if cand in blocked.get(1, set()):
                        continue
                    if (pos, cand, 1) in edge_blocked:
                        continue
                    d = self.world.shortest(cand, task.target)
                    key = (d + (3 if cand in self.world.chokepoints else 0), self.heat.get(cand, 0.0))
                    if key < best_key:
                        best_key = key
                        best_alt = cand
                nxt = best_alt
                path = [pos, nxt]

            # Oscillation breaker: avoid immediate reversal unless strictly necessary.
            if prev_pos is not None and nxt == prev_pos and task.target is not None:
                curr_d = self.world.shortest(pos, task.target)
                rev_d = self.world.shortest(prev_pos, task.target)
                reversing_is_useful = rev_d + 1 < curr_d
                if not reversing_is_useful or osc >= 2:
                    best_alt = None
                    best_key = (10**9, 10**9, 10**9)
                    for cand in self.world.neighbors.get(pos, []):
                        if cand == prev_pos:
                            continue
                        if cand in blocked.get(1, set()):
                            continue
                        if (pos, cand, 1) in edge_blocked:
                            continue
                        d = self.world.shortest(cand, task.target)
                        key = (
                            d,
                            1 if cand in self.world.chokepoints else 0,
                            self.heat.get(cand, 0.0),
                        )
                        if key < best_key:
                            best_key = key
                            best_alt = cand
                    if best_alt is not None:
                        nxt = best_alt
                        path = [pos, nxt]
                    elif not reversing_is_useful:
                        nxt = pos
                        path = [pos, pos]

            self._reserve_path(path, blocked, edge_blocked)
            action = self._move_action(pos, nxt)
            # During prolonged active-order stalls, suppress non-productive traffic.
            if (
                recovery_mode
                and carrying_active_now == 0
                and task.kind in ("staging", "clear_lane", "wait")
                and pos in self.world.chokepoints
            ):
                action = "wait"
            productive = carrying_active_now > 0 or task.kind in ("pickup_active", "deliver", "drop_now")
            if unstick_mode and action.startswith("move_") and not productive:
                if nonproductive_moves >= nonproductive_move_budget:
                    action = "wait"
                else:
                    nonproductive_moves += 1
            action_by_bot[bid] = {"bot": bid, "action": action}

        if advance_round_robin:
            self.round_robin_offset += 1
        return [action_by_bot[b["id"]] for b in bots]

    def _evaluate_actions(self, state: dict, actions: List[dict]) -> float:
        assert self.world is not None
        bots_by_id = {b["id"]: b for b in state["bots"]}
        items_by_id = {it["id"]: it for it in state["items"]}
        active_order, _ = self._active_preview(state["orders"])
        active_need = self._order_need(active_order)
        if not bots_by_id:
            return -10**9

        # Remaining active needs after accounting for currently carried items.
        carried = Counter()
        for b in state["bots"]:
            invc = Counter(b["inventory"])
            for t in active_need:
                carried[t] += min(invc[t], active_need[t])
        remaining = active_need - carried

        # Pickup target cells for still-needed active types.
        pickup_targets: List[Pos] = []
        for it in state["items"]:
            if remaining.get(it["type"], 0) <= 0:
                continue
            shelf = tuple(it["position"])
            pickup_targets.extend(self.world.pickup_adjacency.get(shelf, []))

        score = 0.0
        for a in actions:
            bid = a["bot"]
            act = a.get("action", "wait")
            b = bots_by_id[bid]
            pos = tuple(b["position"])
            inv = b["inventory"]
            invc = Counter(inv)
            carry_active = sum(min(invc[t], active_need[t]) for t in active_need)

            if act == "drop_off":
                if pos in self.world.drop_zones and carry_active > 0:
                    score += 26.0 * carry_active
                else:
                    score -= 3.0
                continue

            if act == "pick_up":
                iid = a.get("item_id")
                it = items_by_id.get(iid)
                if it is None or len(inv) >= 3:
                    score -= 2.0
                    continue
                shelf = tuple(it["position"])
                if abs(pos[0] - shelf[0]) + abs(pos[1] - shelf[1]) != 1:
                    score -= 2.0
                    continue
                typ = it["type"]
                if remaining.get(typ, 0) > 0:
                    score += 18.0
                    remaining[typ] -= 1
                else:
                    score += 2.0
                continue

            if act.startswith("move_"):
                dx, dy = MOVE_DELTAS[act]
                nxt = (pos[0] + dx, pos[1] + dy)
                if nxt not in self.world.walkable:
                    score -= 3.0
                    continue
                if carry_active > 0:
                    old_d = self.world.dist_to_drop.get(pos, 10**9)
                    new_d = self.world.dist_to_drop.get(nxt, 10**9)
                    score += 2.3 * (old_d - new_d)
                elif pickup_targets:
                    old_d = self.world.min_dist_to_any(pos, pickup_targets)
                    new_d = self.world.min_dist_to_any(nxt, pickup_targets)
                    score += 1.2 * (old_d - new_d)
                if nxt in self.world.chokepoints:
                    score -= 0.6
                continue

            # wait
            score -= 0.8
            if pos in self.world.chokepoints:
                score -= 0.6

        # Strong bonus for actions likely to satisfy currently missing active items.
        score += 8.0 * (sum(active_need.values()) - sum(max(0, v) for v in remaining.values()))
        return score

    @staticmethod
    def _action_target_pos(pos: Pos, action: dict) -> Pos:
        act = action.get("action", "wait")
        if act.startswith("move_"):
            dx, dy = MOVE_DELTAS[act]
            return (pos[0] + dx, pos[1] + dy)
        return pos

    def _simulate_positions_one_step(self, positions: Dict[int, Pos], actions_by_bot: Dict[int, dict]) -> Tuple[Dict[int, Pos], int]:
        assert self.world is not None
        # Simulate move resolution in bot id order (matching server behavior).
        cur = dict(positions)
        occupied: Counter = Counter(cur.values())
        blocked_moves = 0
        for bid in sorted(cur.keys()):
            action = actions_by_bot.get(bid, {"bot": bid, "action": "wait"})
            act = action.get("action", "wait")
            if not act.startswith("move_"):
                continue
            pos = cur[bid]
            dx, dy = MOVE_DELTAS[act]
            nxt = (pos[0] + dx, pos[1] + dy)
            if nxt not in self.world.walkable:
                blocked_moves += 1
                continue
            if nxt != pos and occupied[nxt] > 0:
                blocked_moves += 1
                continue
            occupied[pos] -= 1
            if occupied[pos] <= 0:
                del occupied[pos]
            occupied[nxt] += 1
            cur[bid] = nxt
        return cur, blocked_moves

    def _step_score_for_assigned(
        self,
        state: dict,
        assigned: Dict[int, Task],
        before_pos: Dict[int, Pos],
        after_pos: Dict[int, Pos],
        actions_by_bot: Dict[int, dict],
        blocked_moves: int,
    ) -> float:
        assert self.world is not None
        active_order, _ = self._active_preview(state["orders"])
        active_need = self._order_need(active_order)
        bots_by_id = {b["id"]: b for b in state["bots"]}

        score = -2.4 * blocked_moves
        for bid, before in before_pos.items():
            after = after_pos.get(bid, before)
            task = assigned.get(bid, Task(kind="wait", target=before))
            act = actions_by_bot.get(bid, {"action": "wait"}).get("action", "wait")
            target = task.target if task.target is not None else before
            before_d = self.world.shortest(before, target)
            after_d = self.world.shortest(after, target)
            score += 1.6 * (before_d - after_d)
            if act == "wait":
                if task.kind in ("pickup_active", "deliver", "drop_now"):
                    score -= 1.5
                else:
                    score -= 0.2
            if after in self.world.chokepoints and task.kind in ("staging", "clear_lane", "wait"):
                score -= 0.8

            if act == "drop_off":
                invc = Counter(bots_by_id.get(bid, {}).get("inventory", []))
                carry_active = sum(min(invc[t], active_need[t]) for t in active_need)
                if before in self.world.drop_zones and carry_active > 0:
                    score += 14.0 + 4.0 * carry_active
                else:
                    score -= 1.0
            elif act == "pick_up":
                score += 7.5
        return score

    def _candidate_actions_for_bot(
        self,
        state: dict,
        bid: int,
        pos: Pos,
        task: Task,
        base_action: Optional[dict],
        depth: int,
    ) -> List[dict]:
        assert self.world is not None
        options: List[dict] = []
        seen = set()

        def add(a: dict) -> None:
            key = (a.get("action"), a.get("item_id"))
            if key in seen:
                return
            seen.add(key)
            options.append(a)

        if depth == 0 and base_action is not None:
            add(dict(base_action))

        # Keep high-value direct actions available.
        if depth == 0 and task.kind in ("drop_now", "deliver") and pos in self.world.drop_zones:
            add({"bot": bid, "action": "drop_off"})
        if depth == 0 and task.kind in ("pickup_active", "pickup_preview") and task.item_id is not None and task.shelf_pos is not None:
            if self._adjacent(pos, task.shelf_pos):
                add({"bot": bid, "action": "pick_up", "item_id": task.item_id})

        target = task.target if task.target is not None else pos
        ranked_moves = []
        for n in self.world.neighbors.get(pos, []):
            d = self.world.shortest(n, target)
            heat = self.heat.get(n, 0.0)
            choke = 1 if n in self.world.chokepoints else 0
            ranked_moves.append((d + 0.25 * heat + 0.7 * choke, n))
        ranked_moves.sort(key=lambda x: x[0])

        for _, n in ranked_moves[:2]:
            dx = n[0] - pos[0]
            dy = n[1] - pos[1]
            act = DELTA_TO_MOVE.get((dx, dy))
            if act:
                add({"bot": bid, "action": act})
        add({"bot": bid, "action": "wait"})
        return options

    def _rolling_beam_refine(
        self,
        state: dict,
        assigned: Dict[int, Task],
        base_actions: List[dict],
        start_time: float,
    ) -> Tuple[List[dict], int, float]:
        assert self.world is not None
        bots = sorted(state["bots"], key=lambda b: b["id"])
        bots_by_id = {b["id"]: b for b in bots}
        base_by_bot = {a["bot"]: a for a in base_actions}
        initial_positions = {b["id"]: tuple(b["position"]) for b in bots}

        remaining_ms = self.decision_budget_ms - (time.perf_counter() - start_time) * 1000.0
        if remaining_ms < 35.0:
            return base_actions, 0, self._evaluate_actions(state, base_actions)

        horizon = 2 if remaining_ms >= 220.0 else 1
        beam_width = 6 if remaining_ms >= 180.0 else 4
        samples_per_node = 6 if remaining_ms >= 240.0 else 4

        class Node:
            __slots__ = ("positions", "score", "first_actions")

            def __init__(self, positions: Dict[int, Pos], score: float, first_actions: Optional[Dict[int, dict]]):
                self.positions = positions
                self.score = score
                self.first_actions = first_actions

        beam = [Node(initial_positions, 0.0, None)]
        expansions = 0

        urgency = {
            "drop_now": 0,
            "deliver": 1,
            "pickup_active": 2,
            "clear_lane": 3,
            "pickup_preview": 4,
            "staging": 5,
            "wait": 6,
        }
        ordered_ids = sorted(bots_by_id.keys(), key=lambda bid: urgency.get(assigned.get(bid, Task(kind="wait")).kind, 9))

        for depth in range(horizon):
            if (time.perf_counter() - start_time) * 1000.0 >= self.decision_budget_ms * 0.96:
                break
            expanded: List[Node] = []
            for node in beam:
                if (time.perf_counter() - start_time) * 1000.0 >= self.decision_budget_ms * 0.96:
                    break
                for _ in range(samples_per_node):
                    if (time.perf_counter() - start_time) * 1000.0 >= self.decision_budget_ms * 0.96:
                        break
                    expansions += 1
                    joint: Dict[int, dict] = {}
                    soft_reserved: Set[Pos] = set()
                    for bid in ordered_ids:
                        pos = node.positions[bid]
                        task = assigned.get(bid, Task(kind="wait", target=pos))
                        base_action = base_by_bot.get(bid) if depth == 0 else None
                        cands = self._candidate_actions_for_bot(state, bid, pos, task, base_action, depth)
                        scored_cands = []
                        for c in cands:
                            tpos = self._action_target_pos(pos, c)
                            crowd_pen = 1.6 if tpos in soft_reserved and tpos != pos else 0.0
                            target = task.target if task.target is not None else pos
                            d_before = self.world.shortest(pos, target)
                            d_after = self.world.shortest(tpos, target)
                            improve = d_before - d_after
                            w = improve - crowd_pen
                            if c.get("action") == "wait":
                                w -= 0.4
                            scored_cands.append((w, c, tpos))
                        scored_cands.sort(key=lambda x: x[0], reverse=True)
                        pick_idx = 0 if random.random() < 0.72 else min(len(scored_cands) - 1, random.randint(0, min(2, len(scored_cands) - 1)))
                        chosen = scored_cands[pick_idx][1]
                        chosen_tpos = scored_cands[pick_idx][2]
                        joint[bid] = chosen
                        if chosen_tpos != pos:
                            soft_reserved.add(chosen_tpos)

                    next_positions, blocked = self._simulate_positions_one_step(node.positions, joint)
                    step_score = self._step_score_for_assigned(state, assigned, node.positions, next_positions, joint, blocked)
                    first_actions = joint if node.first_actions is None else node.first_actions
                    expanded.append(Node(next_positions, node.score + step_score, first_actions))
            if not expanded:
                break
            expanded.sort(key=lambda n: n.score, reverse=True)
            beam = expanded[:beam_width]

        if not beam or beam[0].first_actions is None:
            return base_actions, expansions, self._evaluate_actions(state, base_actions)
        best = beam[0]
        best_actions = [best.first_actions[b["id"]] for b in bots]
        best_score = self._evaluate_actions(state, best_actions)
        return best_actions, expansions, best_score

    def decide_actions(self, state: dict) -> List[dict]:
        t0 = time.perf_counter()
        self._ensure_world(state)
        if self.spawn_pos is None and state.get("bots"):
            # Spawn is shared at game start; use it as opening decongestion anchor.
            self.spawn_pos = tuple(state["bots"][0]["position"])
            self._build_spread_targets()
        self._decay_and_update_heat(state["bots"])
        self._update_stuck_tracking(state["bots"])
        cur_active_idx = int(state.get("active_order_index", 0))
        if self.prev_active_idx is None or cur_active_idx != self.prev_active_idx:
            self.active_stall_rounds = 0
        else:
            self.active_stall_rounds += 1
        self.prev_active_idx = cur_active_idx
        state["_active_stall_rounds"] = self.active_stall_rounds
        rounds_left = max(0, int(state.get("max_rounds", 300)) - int(state.get("round", 0)))
        if rounds_left <= 20:
            state["_endgame_phase"] = "sprint"
        elif rounds_left <= 100:
            state["_endgame_phase"] = "focus"
        else:
            state["_endgame_phase"] = "normal"

        candidates = self._make_candidates(state)
        assigned = self._assign_tasks(state, candidates, jitter=0.0, shuffle_order=False)
        base_actions = self._actions_from_assignments(
            state,
            assigned,
            planning_offset=self.round_robin_offset,
            advance_round_robin=False,
        )
        base_score = self._evaluate_actions(state, base_actions)

        use_beam = state.get("_endgame_phase") in ("normal", "focus")
        use_beam = use_beam and self.decision_budget_ms >= 220.0
        if use_beam:
            beam_actions, expansions, beam_score = self._rolling_beam_refine(state, assigned, base_actions, t0)
            # Conservative acceptance: beam must clearly improve baseline.
            if beam_score >= base_score + 1.0:
                best_actions = beam_actions
                best_score = beam_score
                accepted = 1
            else:
                best_actions = base_actions
                best_score = base_score
                accepted = 0
        else:
            best_actions = base_actions
            best_score = base_score
            expansions = 0
            accepted = 0

        self.round_robin_offset += 1
        actions = best_actions
        state["_anytime_iters"] = expansions
        state["_anytime_score"] = round(best_score, 2)
        state["_anytime_accepted"] = accepted
        state["_base_score"] = round(base_score, 2)
        state["_decision_ms"] = (time.perf_counter() - t0) * 1000.0
        return actions


class TerminalRenderer:
    def __init__(self, clear_screen: bool = True):
        self.clear_screen = clear_screen
        self.type_chars: Dict[str, str] = {}
        self.palette = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    @staticmethod
    def _order_need(order: Optional[dict]) -> Counter:
        if not order:
            return Counter()
        req = Counter(order["items_required"])
        delivered = Counter(order["items_delivered"])
        out = req - delivered
        for k in list(out.keys()):
            if out[k] <= 0:
                del out[k]
        return out

    @staticmethod
    def _active_preview(orders: List[dict]) -> Tuple[Optional[dict], Optional[dict]]:
        active = None
        preview = None
        for o in orders:
            if o.get("status") == "active":
                active = o
            elif o.get("status") == "preview":
                preview = o
        return active, preview

    def _type_symbol(self, item_type: str) -> str:
        if item_type in self.type_chars:
            return self.type_chars[item_type]
        idx = len(self.type_chars)
        ch = self.palette[idx] if idx < len(self.palette) else "?"
        self.type_chars[item_type] = ch
        return ch

    @staticmethod
    def _bot_symbol(bot_id: int) -> str:
        palette = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if 0 <= bot_id < len(palette):
            return palette[bot_id]
        return "*"

    @staticmethod
    def _format_counter(counter: Counter, limit: int = 8) -> str:
        if not counter:
            return "-"
        parts = []
        for i, (k, v) in enumerate(counter.items()):
            if i >= limit:
                parts.append("...")
                break
            parts.append(f"{k}:{v}")
        return ", ".join(parts)

    def render(self, state: dict, world: WorldModel, actions: List[dict]) -> None:
        width = world.width
        height = world.height
        grid = [["." for _ in range(width)] for _ in range(height)]

        for x, y in world.walls:
            grid[y][x] = "#"
        for x, y in world.shelves:
            grid[y][x] = "S"
        for x, y in world.drop_zones:
            grid[y][x] = "D"

        for item in state["items"]:
            x, y = tuple(item["position"])
            grid[y][x] = self._type_symbol(item["type"])

        bot_cells: Dict[Pos, List[int]] = defaultdict(list)
        for b in state["bots"]:
            bot_cells[tuple(b["position"])].append(b["id"])
        for (x, y), ids in bot_cells.items():
            grid[y][x] = "+" if len(ids) > 1 else self._bot_symbol(ids[0])

        active, preview = self._active_preview(state["orders"])
        active_need = self._order_need(active)
        preview_need = self._order_need(preview)

        inv_total = 0
        inv_types = Counter()
        for b in state["bots"]:
            inv_total += len(b["inventory"])
            inv_types.update(b["inventory"])

        action_counter = Counter(a["action"] for a in actions)

        out = []
        out.append(
            "round "
            f"{state.get('round', '?')}/{state.get('max_rounds', '?')} "
            f"score={state.get('score', '?')} "
            f"active_idx={state.get('active_order_index', '?')} "
            f"bots={len(state.get('bots', []))}"
        )
        phase = state.get("_endgame_phase")
        if phase and phase != "normal":
            out.append(f"mode: endgame-{phase}")
        if "_active_eta_est" in state:
            out.append(f"active_eta_est: {state['_active_eta_est']}")
        if "_active_stall_rounds" in state:
            out.append(f"active_stall_rounds: {state['_active_stall_rounds']}")
        if state.get("_critical_finish_mode"):
            out.append("mode: critical-finish")
        if state.get("_unstick_mode"):
            out.append("mode: unstick")
        if state.get("_opening_spread_mode"):
            out.append("mode: opening-spread")
        if "_decision_ms" in state:
            out.append(f"decision_ms: {state['_decision_ms']:.1f}")
        if "_anytime_iters" in state:
            out.append(
                "anytime: "
                f"iters={state['_anytime_iters']} "
                f"accepted={state.get('_anytime_accepted', 0)} "
                f"base={state.get('_base_score')} "
                f"eval_score={state.get('_anytime_score')}"
            )
        out.append(
            f"active_need: {self._format_counter(active_need)} | "
            f"preview_need: {self._format_counter(preview_need)}"
        )
        out.append(
            f"inventory: total_items={inv_total} top_types={self._format_counter(inv_types, limit=6)}"
        )
        out.append(
            f"actions: move={sum(v for k, v in action_counter.items() if k.startswith('move_'))} "
            f"pick={action_counter.get('pick_up', 0)} "
            f"drop={action_counter.get('drop_off', 0)} "
            f"wait={action_counter.get('wait', 0)}"
        )
        out.append("")
        out.extend("".join(row) for row in grid)
        out.append("")
        if self.type_chars:
            legend = ", ".join(f"{v}={k}" for k, v in sorted(self.type_chars.items(), key=lambda kv: kv[1]))
            out.append(f"item legend: {legend}")
        out.append("tiles: # wall, . floor, S shelf(no current item), D drop, 0-9/A-Z bots, + stacked")

        if self.clear_screen:
            print("\x1b[2J\x1b[H", end="")
        print("\n".join(out), flush=True)


class GameStats:
    def __init__(self):
        self.rounds_seen = 0
        self.action_counts: Counter = Counter()
        self.total_actions = 0
        self.wait_actions = 0
        self.move_actions = 0
        self.pick_actions = 0
        self.drop_actions = 0

        self.blocked_moves = 0
        self.total_move_attempts = 0

        self.oscillation_events = 0
        self.stuck_bot_rounds = 0
        self.max_stuck_streak = 0
        self._stuck_streak_by_bot: Dict[int, int] = defaultdict(int)

        self._prev_prev_pos: Dict[int, Pos] = {}
        self._prev_pos: Dict[int, Pos] = {}
        self.snapshots: List[dict] = []
        self._snapshot_rounds: Set[int] = {0, 25, 50, 100, 150, 200, 250, 300, 350, 400, 450}
        self._seen_snapshot_rounds: Set[int] = set()

    @staticmethod
    def _order_need(order: Optional[dict]) -> Counter:
        if not order:
            return Counter()
        req = Counter(order.get("items_required", []))
        delivered = Counter(order.get("items_delivered", []))
        out = req - delivered
        for k in list(out.keys()):
            if out[k] <= 0:
                del out[k]
        return out

    @staticmethod
    def _active_preview(orders: List[dict]) -> Tuple[Optional[dict], Optional[dict]]:
        active = None
        preview = None
        for o in orders:
            if o.get("status") == "active":
                active = o
            elif o.get("status") == "preview":
                preview = o
        return active, preview

    @staticmethod
    def _fmt_need(counter: Counter, limit: int = 3) -> str:
        if not counter:
            return "-"
        items = list(counter.items())
        parts = []
        for i, (k, v) in enumerate(items):
            if i >= limit:
                parts.append("...")
                break
            parts.append(f"{k}:{v}")
        return ",".join(parts)

    def observe_snapshot(self, state: dict, actions: List[dict]) -> None:
        round_no = int(state.get("round", 0))
        max_rounds = int(state.get("max_rounds", 0))
        should_capture = (
            round_no in self._snapshot_rounds
            or (max_rounds > 0 and round_no >= max_rounds - 1)
            or (round_no % 100 == 0)
        )
        if not should_capture or round_no in self._seen_snapshot_rounds:
            return
        self._seen_snapshot_rounds.add(round_no)

        active, preview = self._active_preview(state.get("orders", []))
        active_need = self._order_need(active)
        preview_need = self._order_need(preview)
        act_counter = Counter(a.get("action", "wait") for a in actions)
        self.snapshots.append(
            {
                "round": round_no,
                "score": int(state.get("score", 0)),
                "active_idx": int(state.get("active_order_index", 0)),
                "stall": int(state.get("_active_stall_rounds", 0)),
                "active_need": self._fmt_need(active_need),
                "preview_need": self._fmt_need(preview_need),
                "mode": state.get("_endgame_phase", "normal"),
                "critical_finish": bool(state.get("_critical_finish_mode", False)),
                "unstick": bool(state.get("_unstick_mode", False)),
                "opening_spread": bool(state.get("_opening_spread_mode", False)),
                "eta": state.get("_active_eta_est", "?"),
                "move": sum(v for k, v in act_counter.items() if k.startswith("move_")),
                "pick": act_counter.get("pick_up", 0),
                "drop": act_counter.get("drop_off", 0),
                "wait": act_counter.get("wait", 0),
            }
        )

    def observe_transition(
        self,
        prev_positions: Dict[int, Pos],
        curr_positions: Dict[int, Pos],
        prev_actions: Dict[int, str],
    ) -> None:
        for bid, curr in curr_positions.items():
            prev = prev_positions.get(bid)
            if prev is None:
                continue

            # Estimate blocked/failed moves: sent move but position unchanged next round.
            act = prev_actions.get(bid)
            if act and act.startswith("move_"):
                self.total_move_attempts += 1
                if curr == prev:
                    self.blocked_moves += 1

            # Stuck tracking.
            if curr == prev:
                self._stuck_streak_by_bot[bid] += 1
                self.stuck_bot_rounds += 1
                if self._stuck_streak_by_bot[bid] > self.max_stuck_streak:
                    self.max_stuck_streak = self._stuck_streak_by_bot[bid]
            else:
                self._stuck_streak_by_bot[bid] = 0

            # A-B-A oscillation signal from realized positions.
            prev2 = self._prev_prev_pos.get(bid)
            if prev2 is not None and curr == prev2 and curr != prev:
                self.oscillation_events += 1

        self._prev_prev_pos = self._prev_pos.copy()
        self._prev_pos = curr_positions.copy()

    def observe_actions(self, actions: List[dict]) -> None:
        self.rounds_seen += 1
        for a in actions:
            act = a.get("action", "wait")
            self.action_counts[act] += 1
            self.total_actions += 1
            if act == "wait":
                self.wait_actions += 1
            elif act == "pick_up":
                self.pick_actions += 1
            elif act == "drop_off":
                self.drop_actions += 1
            elif act.startswith("move_"):
                self.move_actions += 1

    def render_summary(self) -> str:
        total = max(1, self.total_actions)
        move_attempts = max(1, self.total_move_attempts)
        most_common = ", ".join(f"{k}:{v}" for k, v in self.action_counts.most_common(6))
        lines = [
            "",
            "=== game summary ===",
            f"rounds_seen={self.rounds_seen} total_actions={self.total_actions}",
            (
                "actions "
                f"move={self.move_actions} ({100.0*self.move_actions/total:.1f}%) "
                f"pick={self.pick_actions} ({100.0*self.pick_actions/total:.1f}%) "
                f"drop={self.drop_actions} ({100.0*self.drop_actions/total:.1f}%) "
                f"wait={self.wait_actions} ({100.0*self.wait_actions/total:.1f}%)"
            ),
            f"most_common_actions: {most_common if most_common else '-'}",
            (
                "flow "
                f"blocked_moves={self.blocked_moves}/{self.total_move_attempts} "
                f"({100.0*self.blocked_moves/move_attempts:.1f}%) "
                f"oscillation_events={self.oscillation_events} "
                f"stuck_bot_rounds={self.stuck_bot_rounds} "
                f"max_stuck_streak={self.max_stuck_streak}"
            ),
        ]
        if self.snapshots:
            lines.append("snapshots:")
            for s in sorted(self.snapshots, key=lambda x: x["round"]):
                lines.append(
                    f"r{s['round']} score={s['score']} idx={s['active_idx']} stall={s['stall']} mode={s['mode']} "
                    f"critical={1 if s.get('critical_finish') else 0} "
                    f"unstick={1 if s.get('unstick') else 0} "
                    f"spread={1 if s.get('opening_spread') else 0} "
                    f"eta={s['eta']} "
                    f"need={s['active_need']} preview={s['preview_need']} "
                    f"acts(m/p/d/w)={s['move']}/{s['pick']}/{s['drop']}/{s['wait']}"
                )
        return "\n".join(lines)


async def run_bot(
    ws_url: str,
    render: bool = False,
    clear_screen: bool = True,
    decision_budget_ms: float = 450.0,
) -> None:
    controller = HierarchicalController(reservation_horizon=8, decision_budget_ms=decision_budget_ms)
    renderer = TerminalRenderer(clear_screen=clear_screen) if render else None
    stats = GameStats()
    prev_positions: Optional[Dict[int, Pos]] = None
    prev_actions_by_bot: Optional[Dict[int, str]] = None
    async with websockets.connect(ws_url, max_size=None) as ws:
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)

            if msg.get("type") == "game_over":
                print(
                    f"game_over score={msg.get('score')} rounds={msg.get('rounds_used')} "
                    f"items={msg.get('items_delivered')} orders={msg.get('orders_completed')}"
                )
                print(stats.render_summary())
                break

            if msg.get("type") != "game_state":
                continue

            curr_positions = {b["id"]: tuple(b["position"]) for b in msg["bots"]}
            if prev_positions is not None and prev_actions_by_bot is not None:
                stats.observe_transition(prev_positions, curr_positions, prev_actions_by_bot)

            actions = controller.decide_actions(msg)
            if renderer is not None and controller.world is not None:
                renderer.render(msg, controller.world, actions)
            stats.observe_actions(actions)
            stats.observe_snapshot(msg, actions)
            await ws.send(json.dumps({"actions": actions}))
            prev_positions = curr_positions
            prev_actions_by_bot = {a["bot"]: a.get("action", "wait") for a in actions}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Nightmare grocery bot (hierarchical controller)")
    p.add_argument("--ws-url", required=True, help="WebSocket URL from challenge Play button")
    p.add_argument("--render", action="store_true", help="Render live ASCII map each round")
    p.add_argument("--no-clear", action="store_true", help="Do not clear screen before each render")
    p.add_argument(
        "--decision-budget-ms",
        type=float,
        default=450.0,
        help="Anytime planning budget per round in ms (clamped to 50..580 to fit 300s total budget)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(
        run_bot(
            args.ws_url,
            render=args.render,
            clear_screen=not args.no_clear,
            decision_budget_ms=args.decision_budget_ms,
        )
    )


if __name__ == "__main__":
    main()
