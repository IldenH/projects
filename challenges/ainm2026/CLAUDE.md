# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python bot for the **NM i AI Grocery Bot Challenge 2026** — a multiplayer warehouse logistics optimization challenge. The bot connects via WebSocket to a game server and controls multiple robots to pick items from shelves and deliver them to a dropoff point within a warehouse grid.

**Key Goal**: Maximize score by delivering required items for orders efficiently within round limits.

## Setup & Commands

### Initial Setup
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Bot
Obtain a WebSocket URL from the challenge page (includes auth token):
```bash
WS_URL="wss://game-dev.ainm.no/ws?token=YOUR_TOKEN_HERE" python main.py
```

### Testing & Debugging
- No formal test suite yet; bot is tested against live game server
- To debug: add print statements in `decide_actions()` and `decide_bot_action()`
- Monitor game state messages (game_state, game_over) in stdout

## Architecture

### Game Loop (`play()`)
- Establishes WebSocket connection to game server
- Receives JSON messages with game state
- Calls `decide_actions()` to plan bot moves for the current round
- Sends action responses back to server
- Exits cleanly on `game_over` message

### State Processing
Game state contains:
- **grid**: warehouse layout (width, height, walls, shelves)
- **bots**: array of robots with position, inventory, and ID
- **items**: shelf items with type and position
- **orders**: active/preview orders with required items and delivery status
- **drop_off**: target position for item delivery

### Pathfinding Strategy
The bot uses **BFS (Breadth-First Search)** multi-source distance maps to navigate efficiently:
- `bfs_dist_to_goals()`: Computes shortest distance from any cell to a set of goal cells
- `_get_dropoff_dist()`: Pre-computes distance map from all cells to dropoff (static within a game)
- `_get_shelf_adj_dist()`: Pre-computes distance map to cells adjacent to each shelf
- `_best_step_toward()`: Greedily selects next step that minimizes distance to goal

### Decision Logic
Each bot independently decides its action based on:
1. **If holding items and at dropoff**: Drop items
2. **If holding useful items**: Move toward dropoff using distance maps
3. **If inventory full (3 items)**: Wait (unless empty or all items useless)
4. **If empty inventory**: Pick best reachable item for active/preview orders
   - Selects item with minimum distance to pickup location
   - Avoids collisions by tracking other bots' planned positions

### Caching & Optimization
- Static cache stores distance maps and blocked cell sets per game/grid configuration
- Cache invalidates when grid layout changes (walls, shelves detected)
- Reduces redundant pathfinding computations across decision rounds

### Bot Coordination
- Bots are processed in ID order to ensure deterministic move resolution
- Planned positions are tracked to avoid path collisions
- Items are reserved while bot travels to reduce duplication

## Challenge Documentation

Reference the MCP server for detailed game mechanics:
- `challenge://overview` — Challenge rules and scoring overview
- `challenge://grocery-bot` — Grid mechanics, shelf/wall layout, difficulty levels
- `challenge://endpoint-spec` — WebSocket message format and game state schema
- `challenge://scoring` — Score formula and strategy tips
- `challenge://submission-guide` — Submission process and iteration workflow

Access via MCP search: `mcp__grocery-bot__search_docs` or `mcp__grocery-bot__list_docs`

## Key Algorithms & Functions

| Function | Purpose |
|----------|---------|
| `decide_actions(state)` | Main entry point; plans all bot actions for one round |
| `decide_bot_action(...)` | Individual bot decision logic |
| `bfs_dist_to_goals(goals, blocked, width, height)` | Multi-source BFS distance map |
| `_best_step_toward(start, dist_map, blocked)` | Greedy next step selection |
| `_remaining_counts(order)` | Tracks items still needed for an order |
| `_neighbors(x, y)` | Returns 4-directional adjacent cells |

## Common Improvements

### Pathfinding Enhancements
- Replace BFS with A* for potentially faster pathfinding (heuristic: Manhattan distance)
- Implement dynamic obstacle avoidance (other bots as moving obstacles)
- Consider priority queues for multi-robot task assignment

### Strategy Optimization
- Implement order lookahead: prioritize items for preview orders if they're likely to activate soon
- Optimize bot grouping: assign robots to different shelf regions to parallelize item collection
- Cache invalidation: intelligently preserve cache across similar grid states

### Debugging & Monitoring
- Log bot decisions and chosen actions per round
- Track item reservation state across decisions
- Monitor distance map computation overhead
