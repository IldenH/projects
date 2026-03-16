# Nightmare Grocery Bot (Python)

Hierarchical controller for Grocery Bot Nightmare mode:
- Precomputed walkable graph + all-pairs shortest paths
- Utility-scored global task allocation
- Reservation-based movement planning (cell + edge reservations)
- Inventory-aware batching + preview prefetching

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Run

```bash
python3 nightmare_bot.py --ws-url 'wss://game-dev.ainm.no/ws?token=YOUR_TOKEN'
```

Use extra per-round planning time (anytime search) with:

```bash
python3 nightmare_bot.py --ws-url 'wss://game-dev.ainm.no/ws?token=YOUR_TOKEN' --decision-budget-ms 450
```

## Run with Live Terminal Visualization

```bash
python3 nightmare_bot.py --ws-url 'wss://game-dev.ainm.no/ws?token=YOUR_TOKEN' --render --decision-budget-ms 450
```

Optional: keep scrolling log instead of frame-by-frame redraw:

```bash
python3 nightmare_bot.py --ws-url 'wss://game-dev.ainm.no/ws?token=YOUR_TOKEN' --render --no-clear
```

At game end, the bot also prints a summary with:
- action distribution
- estimated blocked move rate
- oscillation events and stuck streak stats

During the game, render output also includes `anytime: iters=... eval_score=...` to show
how many refinement iterations were evaluated within your per-round budget.

Use the WebSocket URL from the Challenge page Play button.
