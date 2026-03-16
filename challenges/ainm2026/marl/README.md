# Grocery Bot — MARL-PPO System

Three-file system: **recorder → simulator → marl_agent**.

## Files

| File | Purpose |
|------|---------|
| `recorder.py` | Connects to live server, plays greedy bot, saves `.json.gz` replays |
| `simulator.py` | Offline GroceryEnv (gym-like) + replay iterator for training without the server |
| `marl_agent.py` | PPO multi-agent trainer, BC warm-start, and live runner |

## Install

```bash
pip install -r requirements.txt
```

## Quickstart

### Step 1 — Record a few live games for BC warm-start

```bash
python recorder.py --token YOUR_TOKEN --out replays/ --games 3
```

Saves `replays/replay_*.json.gz`.  There's a mandatory 65-second cooldown between games.

### Step 2 — Train offline (with replay warm-start)

```bash
# Medium difficulty, 500 episodes, BC warm-start from replays
python marl_agent.py --difficulty medium --episodes 500 --replays replays/

# Hard difficulty, from scratch
python marl_agent.py --difficulty hard --episodes 1000

# Resume from checkpoint
python marl_agent.py --difficulty medium --episodes 200 --load checkpoints/medium_ep500.pt
```

Training runs entirely offline in the `GroceryEnv` simulator — no API quota consumed.

### Step 3 — Run the trained agent live

```bash
python marl_agent.py --run --difficulty medium --token YOUR_TOKEN --load checkpoints/medium_best.pt
```

---

## Architecture

### Observation (per bot)
```
[bx/W, by/H]                         # normalised position          (2)
[inv_0 ... inv_K]                     # inventory one-hot            (K = n_item_types)
[dx_item/D, dy_item/D, dist_item/D]  # direction to nearest need    (3)
[dx_drop/D, dy_drop/D, dist_drop/D]  # direction to drop-off        (3)
[delivered / required]                # order progress               (1)
                                      # total: 9 + K per bot
```

### Policy
- **Shared weights** across all bots (parameter-sharing MARL)
- FC(obs_dim → 256) → LayerNorm → ReLU → FC(256 → 256) → ReLU
- Actor head: FC(256 → 7)   ← 7 discrete actions
- Critic head: FC(256 → 1)  ← state value

### Reward shaping
| Event | Reward |
|-------|--------|
| Score delta (item +1, order +5) | ×1.0 |
| Item picked up | +0.2 |
| Idle bot penalty | −0.05 |

All bots share the same team reward (cooperative MARL).

### Training
- PPO-clip with GAE(λ=0.95)
- 4 update epochs per rollout
- Behavioural cloning warm-start from greedy replay trajectories

---

## Offline Simulator

`GroceryEnv` procedurally generates stores matching each difficulty tier:

```python
from simulator import GroceryEnv

env = GroceryEnv(difficulty="hard", seed=42)
obs = env.reset()            # list of obs vectors, one per bot
obs, reward, done, info = env.step([0, 2, 4, 1, 6])  # action per bot
state_dict = env.get_state_dict()  # full server-format state
```

Replay loading:
```python
from simulator import iter_replays
for trajectory in iter_replays("replays/"):
    for step in trajectory:
        print(step["round"], step["reward"])
```
