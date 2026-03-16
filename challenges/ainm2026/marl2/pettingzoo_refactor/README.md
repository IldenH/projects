# PettingZoo Refactor Baseline

This folder is an isolated baseline that wraps the existing `GroceryEnv` into a PettingZoo `ParallelEnv`, then trains a shared-policy PPO agent.

## Install

```bash
pip install -r pettingzoo_refactor/requirements.txt
```

## Train

```bash
python pettingzoo_refactor/train_ppo.py --difficulty easy --episodes 300 --rollouts-per-update 8 --entropy-coef 0.005 --il-episodes 80 --il-epochs 5
python pettingzoo_refactor/train_ppo.py --difficulty medium --episodes 500 --rollouts-per-update 8 --entropy-coef 0.005 --il-episodes 120 --il-epochs 5
```

Checkpoints are saved under `pettingzoo_refactor/checkpoints/`.

## Evaluate

```bash
python pettingzoo_refactor/train_ppo.py --difficulty easy --eval-only --load pettingzoo_refactor/checkpoints/easy_best.pt
```

## Notes

- Environment dynamics still come from `simulator.GroceryEnv`.
- Team reward is broadcast to all agents (cooperative setting).
- Action masking is enabled for PPO sampling/evaluation (invalid actions masked out).
- Optional IL warm-start is available via `--il-episodes > 0`.
- This is a clean baseline for comparison against the current non-PettingZoo trainer.
