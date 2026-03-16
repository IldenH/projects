from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

import numpy as np

try:
    from gymnasium.spaces import Box, Discrete
    from pettingzoo import ParallelEnv
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "pettingzoo_refactor requires pettingzoo and gymnasium. "
        "Install with: pip install -r pettingzoo_refactor/requirements.txt"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulator import GroceryEnv


class GroceryParallelEnv(ParallelEnv):
    metadata = {"name": "grocery_parallel_v0", "render_modes": []}

    def __init__(self, difficulty: str = "easy", seed: int | None = None):
        self.sim = GroceryEnv(difficulty=difficulty, seed=seed, map_source="hardcoded")
        self.possible_agents = [f"bot_{i}" for i in range(self.sim.n_bots)]
        self.agents = self.possible_agents[:]

        obs_dim = self.sim.obs_dim
        self._obs_space = Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)
        self._act_space = Discrete(self.sim.N_ACTIONS)

    def observation_space(self, agent: str):
        return self._obs_space

    def action_space(self, agent: str):
        return self._act_space

    def reset(self, seed: int | None = None, options: dict | None = None):
        if seed is not None:
            self.sim.seed = seed
        obs_list = self.sim.reset()
        self.agents = self.possible_agents[:]
        obs = {a: np.asarray(obs_list[i], dtype=np.float32) for i, a in enumerate(self.agents)}
        infos = {a: {} for a in self.agents}
        return obs, infos

    def step(self, actions: dict[str, int]):
        if not self.agents:
            return {}, {}, {}, {}, {}

        joint = [int(actions[a]) for a in self.possible_agents]
        obs_list, team_reward, done, info = self.sim.step(joint)

        obs = {a: np.asarray(obs_list[i], dtype=np.float32) for i, a in enumerate(self.possible_agents)}
        rewards = {a: float(team_reward) for a in self.possible_agents}
        terminations = {a: bool(done) for a in self.possible_agents}
        truncations = {a: False for a in self.possible_agents}
        infos = {
            a: {
                "score": info.get("score", 0),
                "round": info.get("round", 0),
                "score_delta": info.get("score_delta", 0),
            }
            for a in self.possible_agents
        }

        if done:
            self.agents = []
        return obs, rewards, terminations, truncations, infos

    def close(self):
        return None

    def state(self) -> np.ndarray:
        obs = self.sim._get_obs()
        return np.concatenate([np.asarray(x, dtype=np.float32) for x in obs], axis=0)


__all__ = ["GroceryParallelEnv"]
