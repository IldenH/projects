import asyncio
import heapq
import json
import os
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import websockets
from scipy.optimize import linear_sum_assignment

WS_URL = os.environ.get("WS_URL", "wss://game-dev.ainm.no/ws?token=YOUR_TOKEN_HERE")


@dataclass
class Task:
    task_id: str
    task_type: Literal["pickup", "deliver", "reposition", "wait"]
    priority: int  # Higher = more urgent
    target_position: tuple[int, int]
    item_id: Optional[str] = None
    item_type: Optional[str] = None
    is_active_order: bool = True


async def play():
    async with websockets.connect(WS_URL) as ws:
        async for message in ws:
            data = json.loads(message)

            if data["type"] == "game_over":
                print(f"Game over! Score: {data['score']}, Rounds: {data['rounds_used']}")
                break

            if data["type"] == "game_state":
                actions = decide_actions(data)
                await ws.send(json.dumps({"actions": actions}))


def _neighbors(x, y):
    return ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y))


def _move_action(from_pos, to_pos):
    x, y = from_pos
    nx, ny = to_pos
    if nx == x and ny == y - 1:
        return "move_up"
    if nx == x and ny == y + 1:
        return "move_down"
    if nx == x - 1 and ny == y:
        return "move_left"
    if nx == x + 1 and ny == y:
        return "move_right"
    return None


def _heuristic(pos, goals):
    """Manhattan distance heuristic to nearest goal."""
    if not goals:
        return float('inf')
    return min(abs(pos[0] - g[0]) + abs(pos[1] - g[1]) for g in goals)


def astar_dist_to_goals(start, goals, blocked, width, height):
    """A* pathfinding. Returns distance from start to nearest goal and the goal reached."""
    if start in blocked or start in goals:
        return 0 if start in goals else None, None

    goals_set = set(goals)
    open_set = [(0, start)]  # (f_score, position)
    came_from = {}
    g_score = {start: 0}
    h_score = {start: _heuristic(start, goals)}
    visited = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.add(current)

        if current in goals_set:
            return g_score[current], current

        for nx, ny in _neighbors(current[0], current[1]):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            neighbor = (nx, ny)
            if neighbor in blocked or neighbor in visited:
                continue

            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                h = _heuristic(neighbor, goals)
                h_score[neighbor] = h
                f = tentative_g + h
                heapq.heappush(open_set, (f, neighbor))

    return None, None


def astar_dist_map(goals, blocked, width, height):
    """Multi-source A*. Returns dist_map for distance-to-nearest-goal."""
    dist = {}
    for g in goals:
        if g in blocked:
            continue
        dist[g] = 0

    # Priority queue: (distance, position)
    pq = [(0, g) for g in goals if g not in blocked]
    heapq.heapify(pq)
    visited = set()

    while pq:
        d, (x, y) = heapq.heappop(pq)

        if (x, y) in visited:
            continue
        visited.add((x, y))

        if (x, y) not in dist:
            dist[(x, y)] = d

        for nx, ny in _neighbors(x, y):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            np = (nx, ny)
            if np in visited or np in blocked:
                continue
            if np not in dist or d + 1 < dist[np]:
                dist[np] = d + 1
                heapq.heappush(pq, (d + 1, np))

    return dist




def _best_step_toward(start, dist_to_goal, blocked_dynamic):
    """Choose a neighbor that reduces distance (or smallest distance), avoiding dynamic blocks."""
    if start not in dist_to_goal:
        return None
    best = None
    best_d = dist_to_goal[start]
    sx, sy = start
    for nx, ny in _neighbors(sx, sy):
        np = (nx, ny)
        if np in blocked_dynamic:
            continue
        d = dist_to_goal.get(np)
        if d is None:
            continue
        if best is None or d < best_d:
            best = np
            best_d = d
    return best


def _get_adjacent_walkable(shelf_pos, blocked, width, height):
    """Get adjacent walkable cells to a shelf."""
    adj = []
    for nx, ny in _neighbors(shelf_pos[0], shelf_pos[1]):
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked:
            adj.append((nx, ny))
    return adj


def generate_tasks(bots, items, orders, drop_off, reserved_items, static_blocked, width, height):
    """Generate pickup, deliver, and reposition tasks."""
    tasks = []

    # Parse orders
    active = next((o for o in orders if o.get("status") == "active" and not o["complete"]), None)
    preview = next((o for o in orders if o.get("status") == "preview" and not o["complete"]), None)
    remaining_active = _remaining_counts(active) if active else {}
    remaining_preview = _remaining_counts(preview, delivered_field="items_delivered") if preview else {}

    # 1. DELIVER tasks (priority 1000)
    for bot in bots:
        has_useful = any(remaining_active.get(item, 0) > 0 for item in bot["inventory"])
        if has_useful and len(bot["inventory"]) > 0:
            tasks.append(Task(
                task_id=f"deliver_{bot['id']}",
                task_type="deliver",
                priority=1000,
                target_position=tuple(drop_off),
                is_active_order=True
            ))

    # 2. PICKUP tasks for active order (priority 500)
    for item in items:
        if item["id"] in reserved_items:
            continue
        if remaining_active.get(item["type"], 0) > 0:
            adj_cells = _get_adjacent_walkable(tuple(item["position"]), static_blocked, width, height)
            if adj_cells:
                tasks.append(Task(
                    task_id=f"pickup_active_{item['id']}",
                    task_type="pickup",
                    priority=500,
                    target_position=tuple(item["position"]),
                    item_id=item["id"],
                    item_type=item["type"],
                    is_active_order=True
                ))

    # 3. PICKUP tasks for preview order (priority 100)
    for item in items:
        if item["id"] in reserved_items:
            continue
        if remaining_preview.get(item["type"], 0) > 0:
            adj_cells = _get_adjacent_walkable(tuple(item["position"]), static_blocked, width, height)
            if adj_cells:
                tasks.append(Task(
                    task_id=f"pickup_preview_{item['id']}",
                    task_type="pickup",
                    priority=100,
                    target_position=tuple(item["position"]),
                    item_id=item["id"],
                    item_type=item["type"],
                    is_active_order=False
                ))

    return tasks


def compute_cost(bot, task, bot_positions, static_blocked, width, height):
    """Lower cost = better assignment."""
    bot_pos = tuple(bot["position"])
    inventory = bot["inventory"]

    # Constraint violations → infinite cost
    if task.task_type == "pickup" and len(inventory) >= 3:
        return float('inf')
    if task.task_type == "deliver" and len(inventory) == 0:
        return float('inf')

    # Base cost: A* distance
    if task.task_type == "deliver":
        if bot_pos == task.target_position:
            base_cost = 0
        else:
            dist_map = astar_dist_map([task.target_position], static_blocked | bot_positions, width, height)
            base_cost = dist_map.get(bot_pos, 10000)
    elif task.task_type == "pickup":
        adj_cells = _get_adjacent_walkable(task.target_position, static_blocked, width, height)
        if not adj_cells:
            return float('inf')
        dist_map = astar_dist_map(adj_cells, static_blocked | bot_positions, width, height)
        base_cost = dist_map.get(bot_pos, 10000)
    else:  # wait
        return 0

    if base_cost >= 10000:
        return float('inf')

    # Priority bonus (higher priority → lower cost)
    priority_bonus = task.priority / 100.0

    # Congestion penalty
    congestion = sum(1 for other in bot_positions
                     if other != bot_pos and abs(bot_pos[0]-other[0])+abs(bot_pos[1]-other[1]) <= 3)

    return max(0, base_cost - priority_bonus + congestion * 0.5)


def build_cost_matrix(bots, tasks, static_blocked, width, height):
    """NxM matrix where Cost[i][j] = cost(bot i, task j)."""
    bot_positions = {tuple(b["position"]) for b in bots}
    cost_matrix = []
    for bot in bots:
        bot_costs = [compute_cost(bot, task, bot_positions, static_blocked, width, height)
                     for task in tasks]
        cost_matrix.append(bot_costs)
    return cost_matrix


def solve_assignment(cost_matrix, bots, tasks):
    """Optimal assignment using Hungarian algorithm."""
    if not tasks:
        return []

    # Pad with dummy tasks if more bots than tasks
    if len(bots) > len(tasks):
        dummy_count = len(bots) - len(tasks)
        for i in range(dummy_count):
            tasks.append(Task(task_id=f"wait_{i}", task_type="wait",
                            priority=0, target_position=(0, 0)))
            for row in cost_matrix:
                row.append(0)

    # Convert to numpy, replace inf with large number
    cost_array = np.array(cost_matrix, dtype=float)
    cost_array[cost_array == float('inf')] = 999999

    # Hungarian algorithm
    bot_indices, task_indices = linear_sum_assignment(cost_array)

    # Build assignments from Hungarian result
    assignments = []
    for bot_idx, task_idx in zip(bot_indices, task_indices):
        if task_idx < len(tasks) and cost_matrix[bot_idx][task_idx] < 999999:
            assignments.append((bots[bot_idx], tasks[task_idx]))

    return assignments


def coordinate_paths(assignments, static_blocked, width, height):
    """Resolve collisions using bot ID priority."""
    bot_next_steps = {}  # bot_id → (next_pos, action, task)

    for bot, task in assignments:
        bot_id = bot["id"]
        bot_pos = tuple(bot["position"])

        if task.task_type == "deliver":
            if bot_pos == task.target_position:
                bot_next_steps[bot_id] = (bot_pos, "drop_off", task)
            else:
                dist_map = astar_dist_map([task.target_position], static_blocked, width, height)
                next_pos = _best_step_toward(bot_pos, dist_map, static_blocked)
                if next_pos:
                    action = _move_action(bot_pos, next_pos)
                    bot_next_steps[bot_id] = (next_pos, action, task)
                else:
                    bot_next_steps[bot_id] = (bot_pos, "wait", task)

        elif task.task_type == "pickup":
            adj_cells = _get_adjacent_walkable(task.target_position, static_blocked, width, height)
            if bot_pos in adj_cells:
                bot_next_steps[bot_id] = (bot_pos, f"pick_up_{task.item_id}", task)
            else:
                dist_map = astar_dist_map(adj_cells, static_blocked, width, height)
                next_pos = _best_step_toward(bot_pos, dist_map, static_blocked)
                if next_pos:
                    action = _move_action(bot_pos, next_pos)
                    bot_next_steps[bot_id] = (next_pos, action, task)
                else:
                    bot_next_steps[bot_id] = (bot_pos, "wait", task)
        else:  # wait
            bot_next_steps[bot_id] = (bot_pos, "wait", task)

    # Resolve collisions by ID priority
    reserved_positions = set()
    final_actions = {}

    for bot_id in sorted(bot_next_steps.keys()):
        next_pos, action, task = bot_next_steps[bot_id]

        if action in ["drop_off", "wait"] or action.startswith("pick_up"):
            final_actions[bot_id] = (action, task)
            reserved_positions.add(next_pos)
        else:
            # Move action: check collision
            if next_pos in reserved_positions:
                # Get current position
                bot = next((b for b, _ in assignments if b["id"] == bot_id))
                current_pos = tuple(bot["position"])
                final_actions[bot_id] = ("wait", task)
                reserved_positions.add(current_pos)
            else:
                final_actions[bot_id] = (action, task)
                reserved_positions.add(next_pos)

    return final_actions


def decide_actions(state):
    bots = state["bots"]
    items = state["items"]
    orders = state["orders"]
    drop_off = state["drop_off"]
    grid = state["grid"]

    # Build static blocked set
    walls = {tuple(p) for p in grid.get("walls", [])}
    shelves = {tuple(it["position"]) for it in items}
    static_blocked = walls | shelves

    # Track reserved items across calls
    reserved_items = set()

    # 1. Generate tasks
    tasks = generate_tasks(
        bots, items, orders, drop_off, reserved_items,
        static_blocked, grid["width"], grid["height"]
    )

    # 2. Build cost matrix
    cost_matrix = build_cost_matrix(
        bots, tasks, static_blocked, grid["width"], grid["height"]
    )

    # 3. Solve assignment
    assignments = solve_assignment(cost_matrix, bots, tasks)

    # 4. Coordinate paths
    actions_dict = coordinate_paths(
        assignments, static_blocked, grid["width"], grid["height"]
    )

    # 5. Update reserved items
    for bot, task in assignments:
        if task.task_type == "pickup" and task.item_id:
            reserved_items.add(task.item_id)

    # 6. Convert to output format
    actions = []
    for bot in sorted(bots, key=lambda b: b["id"]):
        bot_id = bot["id"]
        action_data = actions_dict.get(bot_id, ("wait", None))
        action_str = action_data[0]

        if action_str.startswith("pick_up_"):
            item_id = action_str.split("_", 2)[2]
            actions.append({"bot": bot_id, "action": "pick_up", "item_id": item_id})
        else:
            actions.append({"bot": bot_id, "action": action_str})

    return actions


def _remaining_counts(order, delivered_field="items_delivered"):
    if not order:
        return {}
    needed = {}
    for t in order.get("items_required", []):
        needed[t] = needed.get(t, 0) + 1
    for t in order.get(delivered_field, []):
        needed[t] = needed.get(t, 0) - 1
    return {k: v for k, v in needed.items() if v > 0}


asyncio.run(play())
