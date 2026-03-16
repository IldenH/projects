"""
marl_agent.py — Grocery Bot agent: imitation learning → PPO fine-tuning.

Training pipeline
─────────────────
Phase 1 — Imitation Learning (IL):
  Run the guided (BFS) policy for N episodes, collect (obs, action) pairs,
  train with cross-entropy. Guaranteed to converge to guided policy level.

Phase 2 — PPO fine-tuning:
  Pure on-policy rollouts (no epsilon mixing). The IL-initialised policy
  already scores, so PPO sees real reward signal from episode 1.

Usage
─────
  # Full pipeline on easy (recommended starting point):
  python marl_agent.py --difficulty easy --il-episodes 300 --ppo-episodes 500

  # Curriculum across all difficulties:
  python marl_agent.py --curriculum --il-episodes 300 --ppo-episodes 500

  # Run trained agent on live server:
  python marl_agent.py --run --url wss://game.ainm.no/ws?token=TOKEN --load checkpoints/expert_best.pt --difficulty expert
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import json
import os
import random
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import Adam

from simulator import (
    GroceryEnv, DIFFICULTY, _needed_types, ITEM_NAMES,
    precompute_item_approach, MAX_INVENTORY,
)

# ──────────────────────────────────────────────────────────────────────────────
# Hyperparameters
# ──────────────────────────────────────────────────────────────────────────────

HP = dict(
    # IL
    il_lr          = 3e-4,
    il_batch_size  = 512,
    il_epochs      = 10,

    # PPO
    gamma          = 0.99,
    gae_lambda     = 0.95,
    clip_eps       = 0.2,
    entropy_coef   = 0.01,
    value_coef     = 0.5,
    ppo_lr         = 1e-4,
    ppo_epochs     = 4,
    ppo_batch_size = 512,
    max_grad_norm  = 0.5,
    aux_bad_action_coef = 0.2,
    hidden_dim     = 128,
    rollouts_per_update = 8,   # collect N episodes before each PPO update

    checkpoint_every = 50,
    live_net_confidence = 0.85,
    live_eval_every_updates = 2,
    live_eval_episodes = 12,
)

def get_obs_dim(difficulty: str = "easy") -> int:
    """obs: pos(2) + inv(16, full ITEM_NAMES) + target_dir(3) + ao_pickup_dir(3) = 24"""
    return 24  # constant across all difficulties

OBS_DIM = 24
N_ACTIONS = GroceryEnv.N_ACTIONS               # 7


# ──────────────────────────────────────────────────────────────────────────────
# Network
# ──────────────────────────────────────────────────────────────────────────────

class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int = OBS_DIM, n_actions: int = N_ACTIONS,
                 hidden: int = HP["hidden_dim"]):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.LayerNorm(hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.actor  = nn.Linear(hidden, n_actions)
        self.critic = nn.Linear(hidden, 1)

    def forward(self, x):
        h = self.trunk(x)
        return self.actor(h), self.critic(h).squeeze(-1)

    def act(self, obs, deterministic=False):
        logits, value = self(obs)
        dist   = torch.distributions.Categorical(logits=logits)
        action = dist.mode if deterministic else dist.sample()
        return action, dist.log_prob(action), dist.entropy(), value


# ──────────────────────────────────────────────────────────────────────────────
# Guided (BFS) policy
# ──────────────────────────────────────────────────────────────────────────────

def guided_action(bot_idx: int, env: GroceryEnv) -> int:
    """
    Batched BFS-guided action: fill inventory before delivering.
    Collects up to 3 needed items per trip (active order first, then preview).
    3x more efficient than 1-item-per-trip strategy.
    """
    state   = env.get_state_dict()
    bot     = state["bots"][bot_idx]
    bx, by  = bot["position"]
    bpos    = (bx, by)
    inv     = bot["inventory"]
    active  = next((o for o in state["orders"] if o["status"] == "active"),  None)
    preview = next((o for o in state["orders"] if o["status"] == "preview"), None)

    needed_active  = list(_needed_types(active))
    needed_preview = list(_needed_types(preview)) if preview else []

    # What active-order items do we still need to pick up?
    remaining_active = list(needed_active)
    for i in inv:
        if i in remaining_active:
            remaining_active.remove(i)

    carrying_active = [i for i in inv if i in set(needed_active)]

    # Must explicitly drop when on drop zone, but only if at least one carried
    # item can currently be delivered; otherwise leave drop zone.
    if inv and bpos == tuple(state["drop_off"]):
        if any(i in needed_active for i in inv):
            return 5

    # Deliver when: full, OR carrying active items and nothing more to pick up
    should_deliver = (
        len(inv) >= 3
        or (carrying_active and not remaining_active)
    )

    if should_deliver and inv:
        e = env._drop_cache.get(bpos)
        if e:
            nc = e[0]
            return {(0,-1):0,(0,1):1,(-1,0):2,(1,0):3}.get((nc[0]-bx, nc[1]-by), 6)

    # Still have slots -- pick up more needed items (active first, then preview)
    target_types = set(remaining_active)
    if not target_types and needed_preview:
        remaining_preview = list(needed_preview)
        for i in inv:
            if i in remaining_preview:
                remaining_preview.remove(i)
        target_types = set(remaining_preview)

    if target_types:
        candidates: list[tuple[int, tuple[int, int]]] = []
        for item in state["items"]:
            if item["type"] not in target_types:
                continue
            e = env._approach_cache.get(item["id"], {}).get(bpos)
            if e:
                candidates.append((e[1], e[0]))
        if candidates:
            candidates.sort(key=lambda x: x[0])
            # Multi-bot spread: don't force every bot onto the single nearest item.
            pick_idx = 0 if env.n_bots <= 1 else min(bot_idx, len(candidates) - 1)
            best_d, best_nc = candidates[pick_idx]
            if best_d == 0:
                return 4  # pick_up
            return {(0,-1):0,(0,1):1,(-1,0):2,(1,0):3}.get(
                (best_nc[0]-bx, best_nc[1]-by), random.randint(0, 3))

    # Nothing to pick up -- deliver whatever we have
    if inv:
        e = env._drop_cache.get(bpos)
        if e:
            nc = e[0]
            return {(0,-1):0,(0,1):1,(-1,0):2,(1,0):3}.get((nc[0]-bx, nc[1]-by), 6)

    return random.randint(0, 3)


def coordinated_actions(env: GroceryEnv, proposals: list[int] | None = None) -> list[int]:
    """
    Build collision-aware joint actions.
    - Sequentially reserves occupied cells to avoid move conflicts.
    - Strongly avoids wait, except when no other valid action exists.
    - If proposals are provided (e.g. PPO policy), valid non-wait proposals are preferred.
    """
    state = env.get_state_dict()
    bots = state["bots"]
    W = state["grid"]["width"]
    H = state["grid"]["height"]
    wall_set = set(map(tuple, state["grid"]["walls"])) | {tuple(i["position"]) for i in state["items"]}
    drop_pos = tuple(state["drop_off"])
    active = next((o for o in state["orders"] if o["status"] == "active"), None)
    preview = next((o for o in state["orders"] if o["status"] == "preview"), None)
    needed_active = list(_needed_types(active))
    needed_preview = list(_needed_types(preview)) if preview else []
    move_delta = {0: (0, -1), 1: (0, 1), 2: (-1, 0), 3: (1, 0)}

    def _needed_counts(order: dict | None) -> dict[str, int]:
        counts: dict[str, int] = {}
        if not order:
            return counts
        for t in order["items_required"]:
            counts[t] = counts.get(t, 0) + 1
        for d in order["items_delivered"]:
            if counts.get(d, 0) > 0:
                counts[d] -= 1
        return {k: v for k, v in counts.items() if v > 0}

    active_required = _needed_counts(active)
    preview_required = _needed_counts(preview)
    allow_preview_pickups = env.difficulty in ("easy", "medium")
    active_pick_deficit = dict(active_required)
    preview_pick_deficit = dict(preview_required)
    for b in bots:
        for t in b["inventory"]:
            if active_pick_deficit.get(t, 0) > 0:
                active_pick_deficit[t] -= 1

    occupied_counts: dict[tuple[int, int], int] = {}
    for b in bots:
        p = tuple(b["position"])
        occupied_counts[p] = occupied_counts.get(p, 0) + 1
    joint_actions: list[int] = [6] * len(bots)

    item_by_id = {item["id"]: item for item in state["items"]}
    planned_active_picks: dict[str, int] = {}
    def _remaining_active_deficit(itype: str) -> int:
        return max(0, active_pick_deficit.get(itype, 0) - planned_active_picks.get(itype, 0))

    def _remaining_preview_deficit(itype: str) -> int:
        return max(0, preview_pick_deficit.get(itype, 0) - planned_preview_picks.get(itype, 0))

    def _predict_pick_type(bot: dict) -> str | None:
        bx, by = bot["position"]
        adjacent = [
            item for item in state["items"]
            if abs(item["position"][0] - bx) + abs(item["position"][1] - by) == 1
        ]
        if not adjacent:
            return None
        for item in adjacent:
            t = item["type"]
            if _remaining_active_deficit(t) > 0:
                return t
        if allow_preview_pickups and not any(v > 0 for v in active_pick_deficit.values()):
            for item in adjacent:
                t = item["type"]
                if _remaining_preview_deficit(t) > 0:
                    return t
        return None

    def _target_types_and_delivery(bot):
        inv = bot["inventory"]
        active_types = {t for t, c in active_required.items() if c > 0}
        active_pick_types = {t for t, c in active_pick_deficit.items() if c > 0}
        carrying_active = [i for i in inv if i in active_types]
        should_deliver = (
            len(inv) >= MAX_INVENTORY
            or bool(carrying_active)
        )
        preview_pick_types = {t for t, c in preview_pick_deficit.items() if c > 0}
        target_types = active_pick_types
        if allow_preview_pickups and not target_types:
            target_types = preview_pick_types
        return should_deliver, target_types

    def _is_valid(bot, action_idx):
        bx, by = bot["position"]
        bpos = (bx, by)
        inv = bot["inventory"]
        if action_idx in move_delta:
            dx, dy = move_delta[action_idx]
            nx, ny = bx + dx, by + dy
            if not (0 <= nx < W and 0 <= ny < H):
                return False
            if (nx, ny) in wall_set or occupied_counts.get((nx, ny), 0) > 0:
                return False
            return True
        if action_idx == 4:  # pick_up
            if len(inv) >= MAX_INVENTORY:
                return False
            t = _predict_pick_type(bot)
            return t is not None
        if action_idx == 5:  # drop_off
            return bpos == drop_pos and any(i in active_required and active_required[i] > 0 for i in inv)
        if action_idx == 6:  # wait
            return True
        return False

    def _distance_objective(pos, should_deliver, target_types, inv):
        if should_deliver and inv:
            e = env._drop_cache.get(pos)
            return e[1] if e else 9999
        best = 9999
        if target_types:
            for iid, cache in env._approach_cache.items():
                item = item_by_id.get(iid)
                if not item or item["type"] not in target_types:
                    continue
                e = cache.get(pos)
                if e and e[1] < best:
                    best = e[1]
        if best < 9999:
            return best
        if inv:
            e = env._drop_cache.get(pos)
            return e[1] if e else 9999
        return 9999

    def _score_action(bot, action_idx):
        bx, by = bot["position"]
        bpos = (bx, by)
        inv = bot["inventory"]
        should_deliver, target_types = _target_types_and_delivery(bot)
        if action_idx == 5:
            return 1_000_000.0
        if action_idx == 4:
            return 200_000.0 if not should_deliver else 50_000.0
        if action_idx in move_delta:
            dx, dy = move_delta[action_idx]
            npos = (bx + dx, by + dy)
            d = _distance_objective(npos, should_deliver, target_types, inv)
            return 10_000.0 - float(d)
        return -1_000_000.0

    # Expert traffic control: cap simultaneous workers to reduce aisle congestion.
    worker_indices: set[int]
    if env.difficulty == "expert":
        candidates: list[tuple[float, int]] = []
        for i, bot in enumerate(bots):
            should_deliver, target_types = _target_types_and_delivery(bot)
            pos = tuple(bot["position"])
            dist = _distance_objective(pos, should_deliver, target_types, bot["inventory"])
            priority = (
                1000.0 if bot["inventory"] else 0.0
            ) + (100.0 if should_deliver else 0.0) - float(dist)
            candidates.append((-priority, i))
        candidates.sort()
        keep = min(4, len(bots))
        worker_indices = {i for _, i in candidates[:keep]}
    else:
        worker_indices = set(range(len(bots)))

    planned_preview_picks: dict[str, int] = {}

    for i, bot in enumerate(bots):
        bpos = tuple(bot["position"])
        if i not in worker_indices and not bot["inventory"]:
            # Non-worker bots disperse from spawn/drop lanes to avoid blocking.
            candidate = None
            for a in (0, 2, 1, 3):  # prefer up/left first
                if _is_valid(bot, a):
                    candidate = a
                    break
            valid = [candidate] if candidate is not None else [6]
        else:
            valid = [a for a in range(7) if _is_valid(bot, a)]
        non_wait_valid = [a for a in valid if a != 6]

        chosen = None
        if proposals is not None:
            pa = proposals[i]
            if pa in non_wait_valid:
                chosen = pa

        if chosen is None:
            pool = non_wait_valid if non_wait_valid else valid
            chosen = max(pool, key=lambda a: _score_action(bot, a))

        joint_actions[i] = chosen
        if chosen in move_delta:
            dx, dy = move_delta[chosen]
            src = bpos
            dst = (bpos[0] + dx, bpos[1] + dy)
            occupied_counts[src] = max(0, occupied_counts.get(src, 0) - 1)
            occupied_counts[dst] = occupied_counts.get(dst, 0) + 1
        elif chosen == 4:
            t = _predict_pick_type(bot)
            if t:
                if _remaining_active_deficit(t) > 0:
                    planned_active_picks[t] = planned_active_picks.get(t, 0) + 1
                else:
                    planned_preview_picks[t] = planned_preview_picks.get(t, 0) + 1

    return joint_actions


def run_guided_episode(env: GroceryEnv, seed: int):
    """Run one guided episode. Returns (obs_list, action_list, score)."""
    env.seed = seed
    obs_list = env.reset()
    all_obs, all_acts = [], []
    done = False
    while not done:
        if env.n_bots > 1:
            # Multi-agent IL: use collision-aware joint search directly.
            acts = coordinated_actions(env, proposals=None)
        else:
            acts = [guided_action(0, env)]
        for obs, act in zip(obs_list, acts):
            all_obs.append(obs)
            all_acts.append(act)
        obs_list, _, done, info = env.step(acts)
    return all_obs, all_acts, info["score"]


# ──────────────────────────────────────────────────────────────────────────────
# Rollout buffer
# ──────────────────────────────────────────────────────────────────────────────

class RolloutBuffer:
    def __init__(self):
        self.obs:       list[torch.Tensor] = []
        self.actions:   list[torch.Tensor] = []
        self.action_masks: list[torch.Tensor] = []
        self.bad_flags: list[torch.Tensor] = []
        self.log_probs: list[torch.Tensor] = []
        self.rewards:   list[float]        = []
        self.values:    list[torch.Tensor] = []
        self.dones:     list[bool]         = []

    def compute_returns(self, last_value, gamma, lam):
        T         = len(self.rewards)
        advantages = torch.zeros(T)
        last_gae  = 0.0
        values    = torch.stack(self.values).detach()
        last_v    = last_value.detach()
        for t in reversed(range(T)):
            nv       = last_v if t == T - 1 else values[t + 1]
            mask     = 1.0 - float(self.dones[t])
            delta    = self.rewards[t] + gamma * nv * mask - values[t]
            last_gae = delta + gamma * lam * mask * last_gae
            advantages[t] = last_gae
        return advantages, advantages + values

    def flatten(self):
        return (
            torch.stack(self.obs),
            torch.stack(self.actions),
            torch.stack(self.action_masks),
            torch.stack(self.bad_flags),
            torch.stack(self.log_probs).detach(),
            torch.stack(self.values).detach(),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Trainer
# ──────────────────────────────────────────────────────────────────────────────

class Trainer:

    def __init__(
        self,
        difficulty: str,
        device: str = "cpu",
        map_source: str = "hardcoded",
    ):
        self.difficulty = difficulty
        self.device     = torch.device(device)
        self.map_source = map_source
        self.n_bots     = DIFFICULTY[difficulty]["n_bots"]
        obs_dim         = get_obs_dim(difficulty)
        self.net        = ActorCritic(obs_dim=obs_dim).to(self.device)
        self.il_opt     = Adam(self.net.parameters(), lr=HP["il_lr"])
        self.ppo_opt    = Adam(self.net.parameters(), lr=HP["ppo_lr"])
        self.env        = GroceryEnv(
            difficulty=difficulty,
            map_source=map_source,
        )
        self.best_score = 0.0
        self.best_live_eval = float("-inf")
        self.scores: list[float] = []

    # ── Phase 1: Imitation Learning ─────────────────────────────────────────

    def imitation_learning(self, n_episodes: int, checkpoint_dir: str = "checkpoints"):
        Path(checkpoint_dir).mkdir(exist_ok=True)
        opt = self.il_opt

        print(f"\nPhase 1 — IL on '{self.difficulty}' ({n_episodes} episodes)…\n")

        all_obs:  list = []
        all_acts: list = []
        guided_scores: list[float] = []

        for ep in range(1, n_episodes + 1):
            obs, acts, score = run_guided_episode(self.env, seed=ep)
            all_obs.extend(obs)
            all_acts.extend(acts)
            guided_scores.append(score)
            if ep % 50 == 0 or ep == n_episodes:
                avg = sum(guided_scores[-20:]) / min(20, len(guided_scores))
                print(f"  Collected {ep:4d}/{n_episodes}  "
                      f"score={score:4.0f}  avg20={avg:5.1f}  "
                      f"transitions={len(all_obs)}")

        # Show what the guided policy actually does
        ac = collections.Counter(all_acts)
        N  = len(all_acts)
        names = ["up","down","left","right","pick","drop","wait"]
        print(f"\n  Guided action distribution ({N} transitions):")
        for i, name in enumerate(names):
            print(f"    {name:6s}: {100*ac[i]/N:5.1f}%")

        print(f"\n  Training on {N} transitions, {HP['il_epochs']} epochs…")
        obs_t  = torch.tensor(all_obs,  dtype=torch.float32, device=self.device)
        acts_t = torch.tensor(all_acts, dtype=torch.long,    device=self.device)

        for epoch in range(1, HP["il_epochs"] + 1):
            idx        = torch.randperm(N, device=self.device)
            total_loss = 0.0
            n_batches  = 0
            for start in range(0, N, HP["il_batch_size"]):
                mb     = idx[start:start + HP["il_batch_size"]]
                logits, _ = self.net(obs_t[mb])
                loss   = F.cross_entropy(logits, acts_t[mb])
                opt.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(self.net.parameters(), HP["max_grad_norm"])
                opt.step()
                total_loss += loss.item(); n_batches += 1
            print(f"  Epoch {epoch:2d}/{HP['il_epochs']}  "
                  f"loss={total_loss/max(n_batches,1):.4f}")

        # Evaluate
        eval_scores = []
        for ep in range(20):
            self.env.seed = 90000 + ep
            obs_list = self.env.reset()
            done = False
            while not done:
                acts = []
                for o in obs_list:
                    ot = torch.tensor(o, dtype=torch.float32, device=self.device)
                    with torch.no_grad():
                        a, _, _, _ = self.net.act(ot, deterministic=True)
                    acts.append(a.item())
                obs_list, _, done, info = self.env.step(acts)
            eval_scores.append(info["score"])

        guided_avg = sum(guided_scores) / len(guided_scores)
        learned_avg = sum(eval_scores) / len(eval_scores)
        print(f"\n  IL complete — guided avg={guided_avg:.1f}  "
              f"learned avg={learned_avg:.1f}")

        if learned_avg > self.best_score:
            self.best_score = learned_avg
            self.save(os.path.join(checkpoint_dir, f"{self.difficulty}_il_best.pt"))

        # Reset PPO optimizer so IL momentum doesn't contaminate fine-tuning
        self.ppo_opt = Adam(self.net.parameters(), lr=HP["ppo_lr"])

    # ── Phase 2: PPO fine-tuning ─────────────────────────────────────────────

    def _collect_ppo_rollout(self, seed: int):
        self.env.seed = seed
        obs_list = self.env.reset()
        buffers  = [RolloutBuffer() for _ in range(self.n_bots)]
        done     = False
        score    = 0.0

        while not done:
            state = self.env.get_state_dict()
            active = next((o for o in state["orders"] if o["status"] == "active"), None)
            preview = next((o for o in state["orders"] if o["status"] == "preview"), None)
            needed_active = set(_needed_types(active))
            needed_preview = set(_needed_types(preview))
            needed_all = needed_active | needed_preview
            occupied = {tuple(b["position"]) for b in state["bots"]}
            prev_positions = [tuple(b["position"]) for b in state["bots"]]

            obs_tensors = [
                torch.tensor(o, dtype=torch.float32, device=self.device)
                for o in obs_list
            ]
            actions_int = []
            for buf, ot, bot in zip(buffers, obs_tensors, state["bots"]):
                bx, by = bot["position"]
                inv = bot["inventory"]
                bpos = (bx, by)
                valid = set()
                # Moves
                for ai, (dx, dy) in [(0, (0, -1)), (1, (0, 1)), (2, (-1, 0)), (3, (1, 0))]:
                    nx, ny = bx + dx, by + dy
                    if 0 <= nx < self.env._map["grid"]["width"] and 0 <= ny < self.env._map["grid"]["height"]:
                        if (nx, ny) not in self.env._wall_set and (nx, ny) not in occupied:
                            valid.add(ai)
                # pick_up
                if len(inv) < MAX_INVENTORY and needed_all:
                    for item in state["items"]:
                        ix, iy = item["position"]
                        if abs(ix - bx) + abs(iy - by) == 1 and item["type"] in needed_all:
                            valid.add(4)
                            break
                # drop_off
                if bpos == tuple(state["drop_off"]) and inv:
                    valid.add(5)
                # wait (only if nothing else is valid)
                if not valid:
                    valid.add(6)

                with torch.no_grad():
                    logits, value = self.net(ot)
                    mask_vec = torch.zeros(GroceryEnv.N_ACTIONS, dtype=torch.bool, device=self.device)
                    for va in valid:
                        mask_vec[va] = True
                    masked_logits = logits.clone()
                    for aidx in range(GroceryEnv.N_ACTIONS):
                        if aidx not in valid:
                            masked_logits[aidx] = -1e9
                    dist = torch.distributions.Categorical(logits=masked_logits)
                    action = dist.sample()
                    log_prob = dist.log_prob(action)
                actions_int.append(action.item())
                buf.obs.append(ot)
                buf.actions.append(action)
                buf.action_masks.append(mask_vec)
                buf.log_probs.append(log_prob)
                buf.values.append(value)

                # Reserve target so later bots avoid immediate collisions.
                if action.item() in (0, 1, 2, 3):
                    dx, dy = {0: (0, -1), 1: (0, 1), 2: (-1, 0), 3: (1, 0)}[action.item()]
                    occupied.discard((bx, by))
                    occupied.add((bx + dx, by + dy))

            obs_list, reward, done, info = self.env.step(actions_int)
            score = info["score"]
            new_positions = [tuple(b["position"]) for b in self.env.get_state_dict()["bots"]]
            for i, buf in enumerate(buffers):
                a = actions_int[i]
                moved = new_positions[i] != prev_positions[i]
                wait_with_work = (a == 6) and bool(needed_all)
                noop_move = (a in (0, 1, 2, 3)) and (not moved)
                bad_flag = 1.0 if (wait_with_work or noop_move) else 0.0
                buf.bad_flags.append(torch.tensor(bad_flag, dtype=torch.float32, device=self.device))
                buf.rewards.append(reward)
                buf.dones.append(done)

        return buffers, score

    def _ppo_update(self, buffers: list[RolloutBuffer]) -> dict:
        gamma, lam = HP["gamma"], HP["gae_lambda"]
        clip       = HP["clip_eps"]
        opt        = self.ppo_opt

        all_obs, all_acts, all_masks, all_bad, all_logps = [], [], [], [], []
        all_vals, all_advs, all_rets = [], [], []

        for buf in buffers:
            if not buf.rewards:
                continue
            # Bootstrap from the last stored observation in this buffer
            with torch.no_grad():
                _, lv = self.net(buf.obs[-1])
            advs, rets = buf.compute_returns(lv, gamma, lam)
            obs_t, acts_t, masks_t, bad_t, logps_t, vals_t = buf.flatten()
            all_obs.append(obs_t);     all_acts.append(acts_t)
            all_masks.append(masks_t)
            all_bad.append(bad_t)
            all_logps.append(logps_t); all_vals.append(vals_t)
            all_advs.append(advs);     all_rets.append(rets)

        if not all_obs:
            return {}

        obs      = torch.cat(all_obs).to(self.device)
        acts     = torch.cat(all_acts).to(self.device)
        masks    = torch.cat(all_masks).to(self.device)
        bad_flags = torch.cat(all_bad).to(self.device)
        logps    = torch.cat(all_logps).to(self.device)
        advs     = torch.cat(all_advs).to(self.device)
        rets     = torch.cat(all_rets).to(self.device)
        old_vals = torch.cat(all_vals).to(self.device)

        advs = (advs - advs.mean()) / (advs.std() + 1e-8)

        N, bs = obs.shape[0], HP["ppo_batch_size"]
        stats = {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "aux_bad": 0.0}
        n_upd = 0

        for _ in range(HP["ppo_epochs"]):
            idx = torch.randperm(N, device=self.device)
            for start in range(0, N, bs):
                mb      = idx[start:start+bs]
                logits, values = self.net(obs[mb])
                masked_logits = logits.masked_fill(~masks[mb].bool(), -1e9)
                dist    = torch.distributions.Categorical(logits=masked_logits)
                new_lps = dist.log_prob(acts[mb])
                entropy = dist.entropy().mean()

                ratio = (new_lps - logps[mb]).exp()
                s1 = ratio * advs[mb]
                s2 = ratio.clamp(1-clip, 1+clip) * advs[mb]
                p_loss = -torch.min(s1, s2).mean()

                v_clipped = old_vals[mb] + (values - old_vals[mb]).clamp(-clip, clip)
                v_loss = torch.max(F.mse_loss(values, rets[mb]),
                                   F.mse_loss(v_clipped, rets[mb]))

                taken_prob = dist.probs.gather(1, acts[mb].unsqueeze(1)).squeeze(1)
                aux_bad = (taken_prob * bad_flags[mb]).mean()

                loss = (
                    p_loss
                    + HP["value_coef"] * v_loss
                    - HP["entropy_coef"] * entropy
                    + HP["aux_bad_action_coef"] * aux_bad
                )
                opt.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(self.net.parameters(), HP["max_grad_norm"])
                opt.step()

                stats["policy_loss"] += p_loss.item()
                stats["value_loss"]  += v_loss.item()
                stats["entropy"]     += entropy.item()
                stats["aux_bad"]     += aux_bad.item()
                n_upd += 1

        if n_upd:
            for k in stats:
                stats[k] /= n_upd
        return stats

    def evaluate_live_style(
        self,
        n_episodes: int | None = None,
        seed_base: int = 700000,
    ) -> tuple[float, float]:
        """
        Evaluate using live-style hybrid decision logic on simulator states.
        This mirrors deployment policy closer than raw PPO rollout scores.
        """
        n_eval = n_episodes if n_episodes is not None else HP["live_eval_episodes"]
        act_to_idx = {name: i for i, name in enumerate(GroceryEnv.ACTION_NAMES)}
        conf_thr = HP["live_net_confidence"]

        def _build_drop(drop, walls, w, h):
            from collections import deque
            dist = {drop: 0}
            parent = {drop: drop}
            q = deque([drop])
            while q:
                pos = q.popleft()
                x, y = pos
                for nx, ny in [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]:
                    npos = (nx, ny)
                    if npos in dist or not (0 <= nx < w and 0 <= ny < h) or npos in walls:
                        continue
                    dist[npos] = dist[pos] + 1
                    parent[npos] = pos
                    q.append(npos)
            return {p: (parent[p], dist[p]) for p in dist}

        def _bot_obs(bot, needed_active, needed_preview, state, approach_cache, drop_cache, W, H):
            D = max(W, H)
            bx, by = bot["position"]
            bpos = (bx, by)
            inv = bot["inventory"]
            needed_set = set(needed_active)

            pos = [bx / W, by / H]
            full_type_idx = {t: i for i, t in enumerate(ITEM_NAMES)}
            inv_vec = [0.0] * len(ITEM_NAMES)
            for itype in inv:
                idx = full_type_idx.get(itype)
                if idx is not None:
                    inv_vec[idx] = min(1.0, inv_vec[idx] + 1.0)

            remaining_active = list(needed_active)
            for i in inv:
                if i in remaining_active:
                    remaining_active.remove(i)
            carrying_active = [i for i in inv if i in needed_set]
            should_deliver = len(inv) >= MAX_INVENTORY or (bool(carrying_active) and not remaining_active)

            target_types = set(remaining_active)
            if not target_types and needed_preview:
                remaining_preview = list(needed_preview)
                for i in inv:
                    if i in remaining_preview:
                        remaining_preview.remove(i)
                target_types = set(remaining_preview)

            best_dist, best_next = 9999, bpos
            for item in state["items"]:
                if item["type"] not in target_types:
                    continue
                entry = approach_cache.get(item["id"], {}).get(bpos)
                if entry and entry[1] < best_dist:
                    best_dist, best_next = entry[1], entry[0]
            pickup_dir = (
                [(best_next[0] - bx) / D, (best_next[1] - by) / D, best_dist / (W + H)]
                if best_dist < 9999 else [0.0, 0.0, 1.0]
            )

            ao_dist, ao_next = 9999, bpos
            for item in state["items"]:
                if item["type"] not in needed_set:
                    continue
                entry = approach_cache.get(item["id"], {}).get(bpos)
                if entry and entry[1] < ao_dist:
                    ao_dist, ao_next = entry[1], entry[0]
            ao_pickup_dir = (
                [(ao_next[0] - bx) / D, (ao_next[1] - by) / D, ao_dist / (W + H)]
                if ao_dist < 9999 else [0.0, 0.0, 1.0]
            )

            drop_entry = drop_cache.get(bpos)
            drop_dir_vec = (
                [(drop_entry[0][0] - bx) / D, (drop_entry[0][1] - by) / D, drop_entry[1] / (W + H)]
                if drop_entry else [0.0, 0.0, 1.0]
            )
            target_dir = drop_dir_vec if should_deliver else pickup_dir
            return pos + inv_vec + target_dir + ao_pickup_dir

        def _is_valid_action(bot, action, state, needed_active, needed_preview, occupied_now, wall_set, W, H):
            bx, by = bot["position"]
            inv = bot["inventory"]
            if action == "drop_off":
                return tuple(bot["position"]) == tuple(state["drop_off"]) and bool(inv)
            if action == "pick_up":
                if len(inv) >= MAX_INVENTORY:
                    return False
                needed = set(needed_active) | set(needed_preview)
                if not needed:
                    return False
                for item in state["items"]:
                    ix, iy = item["position"]
                    if abs(ix - bx) + abs(iy - by) == 1 and item["type"] in needed:
                        return True
                return False
            if action in ("move_up", "move_down", "move_left", "move_right"):
                delta = {
                    "move_up": (0, -1), "move_down": (0, 1),
                    "move_left": (-1, 0), "move_right": (1, 0),
                }[action]
                nx, ny = bx + delta[0], by + delta[1]
                if not (0 <= nx < W and 0 <= ny < H):
                    return False
                if (nx, ny) in wall_set or (nx, ny) in occupied_now:
                    return False
                return True
            if action == "wait":
                return not needed_active and not needed_preview
            return False

        scores = []
        for ep in range(n_eval):
            self.env.seed = seed_base + ep
            self.env.reset()

            state = self.env.get_state_dict()
            W = state["grid"]["width"]
            H = state["grid"]["height"]
            wall_set = set(map(tuple, state["grid"]["walls"])) | {tuple(i["position"]) for i in state["items"]}
            drop_cache = _build_drop(tuple(state["drop_off"]), wall_set, W, H)
            approach_cache: dict[str, dict] = {}
            stuck_history: dict[int, list[tuple[int, int]]] = {}

            done = False
            info = {"score": 0}
            while not done:
                state = self.env.get_state_dict()
                active = next((o for o in state["orders"] if o["status"] == "active"), None)
                preview = next((o for o in state["orders"] if o["status"] == "preview"), None)
                needed_active = list(_needed_types(active))
                needed_preview = list(_needed_types(preview)) if preview else []

                for item in state["items"]:
                    if item["id"] not in approach_cache:
                        approach_cache[item["id"]] = precompute_item_approach(
                            tuple(item["position"]), wall_set, W, H
                        )

                occupied_now = {tuple(b["position"]) for b in state["bots"]}
                joint_actions: list[int] = []

                for bot in state["bots"]:
                    bx, by = bot["position"]
                    bpos = (bx, by)
                    inv = bot["inventory"]
                    needed_set = set(needed_active)
                    bot_id = bot["id"]

                    hist = stuck_history.setdefault(bot_id, [])
                    hist.append(bpos)
                    if len(hist) > 6:
                        hist.pop(0)
                    is_stuck = len(hist) >= 4 and len(set(hist[-4:])) == 1

                    if bpos == tuple(state["drop_off"]) and inv:
                        action_name = "drop_off"
                        joint_actions.append(act_to_idx[action_name])
                        continue

                    obs = _bot_obs(bot, needed_active, needed_preview, state, approach_cache, drop_cache, W, H)
                    ot = torch.tensor(obs, dtype=torch.float32, device=self.device)
                    with torch.no_grad():
                        logits, _ = self.net(ot)
                        probs = torch.softmax(logits, dim=-1)
                        conf, a = torch.max(probs, dim=-1)
                    proposed = GroceryEnv.ACTION_NAMES[a.item()]
                    net_conf = float(conf.item())

                    valid_model_action = _is_valid_action(
                        bot, proposed, state, needed_active, needed_preview, occupied_now, wall_set, W, H
                    )
                    use_net = valid_model_action and not is_stuck and net_conf >= conf_thr
                    if use_net:
                        action_name = proposed
                    else:
                        remaining_active = list(needed_active)
                        for i in inv:
                            if i in remaining_active:
                                remaining_active.remove(i)
                        carrying_active = [i for i in inv if i in needed_set]
                        should_deliver = len(inv) >= MAX_INVENTORY or (bool(carrying_active) and not remaining_active)
                        if len(inv) >= MAX_INVENTORY and not carrying_active:
                            should_deliver = True

                        action_name = "wait"
                        if should_deliver and inv and bpos in drop_cache:
                            nc = drop_cache[bpos][0]
                            action_name = {
                                (0, -1): "move_up", (0, 1): "move_down",
                                (-1, 0): "move_left", (1, 0): "move_right",
                            }.get((nc[0] - bx, nc[1] - by), "wait")
                        else:
                            target_types = set(remaining_active) or set(needed_preview)
                            best_d, best_item, best_nc = 9999, None, None
                            for item in state["items"]:
                                if item["type"] not in target_types:
                                    continue
                                e = approach_cache.get(item["id"], {}).get(bpos)
                                if e and e[1] < best_d:
                                    best_d, best_item, best_nc = e[1], item, e[0]
                            if best_item is not None:
                                if best_d == 0:
                                    action_name = "pick_up"
                                else:
                                    action_name = {
                                        (0, -1): "move_up", (0, 1): "move_down",
                                        (-1, 0): "move_left", (1, 0): "move_right",
                                    }.get((best_nc[0] - bx, best_nc[1] - by), "wait")
                            elif inv and bpos in drop_cache:
                                nc = drop_cache[bpos][0]
                                action_name = {
                                    (0, -1): "move_up", (0, 1): "move_down",
                                    (-1, 0): "move_left", (1, 0): "move_right",
                                }.get((nc[0] - bx, nc[1] - by), "wait")
                            elif bpos in drop_cache:
                                nc = drop_cache[bpos][0]
                                action_name = {
                                    (0, -1): "move_up", (0, 1): "move_down",
                                    (-1, 0): "move_left", (1, 0): "move_right",
                                }.get((nc[0] - bx, nc[1] - by), "wait")

                    joint_actions.append(act_to_idx[action_name])
                    if action_name.startswith("move_"):
                        dx, dy = {
                            "move_up": (0, -1), "move_down": (0, 1),
                            "move_left": (-1, 0), "move_right": (1, 0),
                        }[action_name]
                        occupied_now.discard((bx, by))
                        occupied_now.add((bx + dx, by + dy))

                _, _, done, info = self.env.step(joint_actions)

            scores.append(float(info["score"]))

        avg_score = sum(scores) / max(1, len(scores))
        best_score = max(scores) if scores else 0.0
        return avg_score, best_score

    def ppo_finetune(self, n_episodes: int, checkpoint_dir: str = "checkpoints"):
        Path(checkpoint_dir).mkdir(exist_ok=True)
        print(f"\nPhase 2 — PPO on '{self.difficulty}' ({n_episodes} episodes)…\n")

        rpu = HP["rollouts_per_update"]
        update_num = 0

        for ep_start in range(1, n_episodes + 1, rpu):
            t0 = time.time()
            ep_end = min(ep_start + rpu, n_episodes + 1)

            # Collect rpu rollouts before updating
            all_buffers: list[RolloutBuffer] = []
            ep_scores = []
            for ep in range(ep_start, ep_end):
                bufs, score = self._collect_ppo_rollout(seed=ep)
                all_buffers.extend(bufs)
                ep_scores.append(score)
                self.scores.append(score)

            stats = self._ppo_update(all_buffers)
            update_num += 1

            best_ep = max(ep_scores)
            avg_ep  = sum(ep_scores) / len(ep_scores)
            if best_ep > self.best_score:
                self.best_score = best_ep
                self.save(os.path.join(checkpoint_dir, f"{self.difficulty}_train_best.pt"))

            live_eval = None
            if (
                update_num % HP["live_eval_every_updates"] == 0
                or ep_end >= n_episodes + 1
            ):
                live_seed_base = 700000 + update_num * 100
                live_avg, live_best = self.evaluate_live_style(seed_base=live_seed_base)
                live_eval = (live_avg, live_best)
                if live_avg > self.best_live_eval:
                    self.best_live_eval = live_avg
                    self.save(os.path.join(checkpoint_dir, f"{self.difficulty}_best.pt"))

            if ep_end % HP["checkpoint_every"] == 1:  # every ~50 episodes
                self.save(os.path.join(checkpoint_dir,
                                       f"{self.difficulty}_ep{ep_end-1}.pt"))

            avg20 = sum(self.scores[-20:]) / min(20, len(self.scores))
            print(
                f"Ep {ep_end-1:4d}/{n_episodes}  "
                f"batch_avg={avg_ep:5.1f}  avg20={avg20:5.1f}  "
                f"π={stats.get('policy_loss',0):+.3f}  "
                f"v={stats.get('value_loss',0):.3f}  "
                f"H={stats.get('entropy',0):.3f}  "
                f"aux={stats.get('aux_bad',0):.3f}  "
                + (f"  live_avg={live_eval[0]:5.1f}" if live_eval is not None else "")
                + f"  t={time.time()-t0:.2f}s"
            )

        print(f"\nPPO complete. Train best: {self.best_score:.0f}  Live-eval best avg: {self.best_live_eval:.1f}")

    # ── Save / load ──────────────────────────────────────────────────────────

    def save(self, path: str):
        torch.save({"net": self.net.state_dict(), "best_score": self.best_score,
                    "difficulty": self.difficulty, "scores": self.scores,
                    "obs_dim": OBS_DIM}, path)
        print(f"  → {path}")

    def load(self, path: str):
        ckpt = torch.load(path, map_location=self.device)
        saved_obs_dim = ckpt.get("obs_dim", None)
        if saved_obs_dim is not None and saved_obs_dim != OBS_DIM:
            raise ValueError(
                f"Checkpoint obs_dim={saved_obs_dim} != current OBS_DIM={OBS_DIM}. "
                f"Delete old checkpoints and retrain from scratch."
            )
        self.net.load_state_dict(ckpt["net"])
        self.best_score = ckpt.get("best_score", 0)
        self.scores     = ckpt.get("scores", [])
        print(f"Loaded '{path}' (best={self.best_score:.0f})")


# ──────────────────────────────────────────────────────────────────────────────
# Live runner
# ──────────────────────────────────────────────────────────────────────────────

async def run_live(url: str, trainer: Trainer):
    import websockets
    import time as _time
    from collections import deque as _deque

    ACT_STRS = GroceryEnv.ACTION_NAMES

    drop_cache: dict = {}; approach_cache: dict = {}
    W = H = D = 0; wall_set: set = set()
    round_times: list[float] = []
    prev_score = 0
    stuck_history: dict[int, list] = {}   # bot_id -> last 5 positions
    stuck_counts:  dict[int, int]  = {}   # bot_id -> total stuck rescues

    def _guided_live(bpos, inv, needed_active, needed_preview,
                     approach_cache, drop_cache, wall_set, W, H):
        """Pure BFS guided action for stuck-bot fallback."""
        bx, by = bpos
        needed_set = set(needed_active)
        remaining = list(needed_active)
        for i in inv:
            if i in remaining: remaining.remove(i)
        carrying = [i for i in inv if i in needed_set]
        should_deliver = len(inv) >= MAX_INVENTORY or (bool(carrying) and not remaining)

        if should_deliver and inv:
            e = drop_cache.get(bpos)
            if e: return {(0,-1):'move_up',(0,1):'move_down',(-1,0):'move_left',(1,0):'move_right'}.get(
                (e[0][0]-bx, e[0][1]-by), 'wait')

        target_types = set(remaining) or set(needed_preview)
        bd, bn = 9999, None
        for iid, cache in approach_cache.items():
            e = cache.get(bpos)
            if e and e[1] < bd:
                bd, bn = e[1], e[0]
        if bn:
            dx, dy = bn[0]-bx, bn[1]-by
            if bd == 0: return 'pick_up'
            return {(0,-1):'move_up',(0,1):'move_down',(-1,0):'move_left',(1,0):'move_right'}.get((dx,dy),'wait')
        if inv:
            e = drop_cache.get(bpos)
            if e: return {(0,-1):'move_up',(0,1):'move_down',(-1,0):'move_left',(1,0):'move_right'}.get(
                (e[0][0]-bx, e[0][1]-by), 'wait')
        import random as _r; return _r.choice(['move_up','move_down','move_left','move_right'])

    def _build_drop(drop, walls, w, h):
        dist={drop:0}; parent={drop:drop}; q=_deque([drop])
        while q:
            pos=q.popleft(); x,y=pos
            for nx,ny in [(x,y-1),(x,y+1),(x-1,y),(x+1,y)]:
                npos=(nx,ny)
                if npos in dist or not(0<=nx<w and 0<=ny<h) or npos in walls: continue
                dist[npos]=dist[pos]+1; parent[npos]=pos; q.append(npos)
        return {p:(parent[p],dist[p]) for p in dist}

    def _bot_obs(bot, needed_active, needed_preview, state):
        bx, by = bot["position"]
        bpos = (bx, by)
        inv = bot["inventory"]
        needed_set = set(needed_active)

        pos = [bx / W, by / H]

        full_type_idx = {t: i for i, t in enumerate(ITEM_NAMES)}
        inv_vec = [0.0] * len(ITEM_NAMES)
        for itype in inv:
            idx = full_type_idx.get(itype)
            if idx is not None:
                inv_vec[idx] = min(1.0, inv_vec[idx] + 1.0)

        remaining_active = list(needed_active)
        for i in inv:
            if i in remaining_active:
                remaining_active.remove(i)
        carrying_active = [i for i in inv if i in needed_set]

        should_deliver = (
            len(inv) >= MAX_INVENTORY
            or (bool(carrying_active) and not remaining_active)
        )

        target_types = set(remaining_active)
        if not target_types and needed_preview:
            remaining_preview = list(needed_preview)
            for i in inv:
                if i in remaining_preview:
                    remaining_preview.remove(i)
            target_types = set(remaining_preview)

        best_dist, best_next = 9999, bpos
        for item in state["items"]:
            if item["type"] not in target_types:
                continue
            entry = approach_cache.get(item["id"], {}).get(bpos)
            if entry and entry[1] < best_dist:
                best_dist, best_next = entry[1], entry[0]

        pickup_dir = (
            [(best_next[0]-bx)/D, (best_next[1]-by)/D, best_dist/(W+H)]
            if best_dist < 9999 else [0.0, 0.0, 1.0]
        )

        ao_dist, ao_next = 9999, bpos
        for item in state["items"]:
            if item["type"] not in needed_set:
                continue
            entry = approach_cache.get(item["id"], {}).get(bpos)
            if entry and entry[1] < ao_dist:
                ao_dist, ao_next = entry[1], entry[0]
        ao_pickup_dir = (
            [(ao_next[0]-bx)/D, (ao_next[1]-by)/D, ao_dist/(W+H)]
            if ao_dist < 9999 else [0.0, 0.0, 1.0]
        )

        drop_entry = drop_cache.get(bpos)
        drop_dir_vec = (
            [(drop_entry[0][0]-bx)/D, (drop_entry[0][1]-by)/D, drop_entry[1]/(W+H)]
            if drop_entry else [0.0, 0.0, 1.0]
        )

        target_dir = drop_dir_vec if should_deliver else pickup_dir
        return pos + inv_vec + target_dir + ao_pickup_dir

    def _is_valid_action(bot, action, needed_active, needed_preview, occupied_now):
        bx, by = bot["position"]
        inv = bot["inventory"]
        if action == "drop_off":
            return tuple(bot["position"]) == tuple(state["drop_off"]) and bool(inv)
        if action == "pick_up":
            if len(inv) >= MAX_INVENTORY:
                return False
            needed = set(needed_active) | set(needed_preview)
            if not needed:
                return False
            for item in state["items"]:
                ix, iy = item["position"]
                if abs(ix - bx) + abs(iy - by) == 1 and item["type"] in needed:
                    return True
            return False
        if action in ("move_up", "move_down", "move_left", "move_right"):
            delta = {
                "move_up": (0, -1),
                "move_down": (0, 1),
                "move_left": (-1, 0),
                "move_right": (1, 0),
            }[action]
            nx, ny = bx + delta[0], by + delta[1]
            if not (0 <= nx < W and 0 <= ny < H):
                return False
            if (nx, ny) in wall_set:
                return False
            if (nx, ny) in occupied_now:
                return False
            return True
        if action == "wait":
            return not needed_active and not needed_preview
        return False

    print(f"Connecting ({trainer.difficulty})…")
    async with websockets.connect(url, ping_interval=20) as ws:
        while True:
            t0 = _time.perf_counter()
            msg = json.loads(await ws.recv())
            if msg["type"] == "game_over":
                avg_ms = sum(round_times)/len(round_times) if round_times else 0
                max_ms = max(round_times) if round_times else 0
                slow   = sum(1 for t in round_times if t > 1500)
                print(f"Game over! Score: {msg['score']}")
                print(f"  Rounds: {len(round_times)}  "
                      f"Response time: avg={avg_ms:.0f}ms  max={max_ms:.0f}ms  slow(>1.5s)={slow}")
                if stuck_counts:
                    print(f"  Guided fallbacks (stuck rescues): {dict(stuck_counts)}")
                break

            state = msg
            rnd   = state.get("round", 0)
            score = state.get("score", 0)

            if not drop_cache:
                W=state["grid"]["width"]; H=state["grid"]["height"]; D=max(W,H)
                grid_wall_set=set(map(tuple,state["grid"]["walls"]))
                wall_set=set(grid_wall_set)
                shelf_set={tuple(i["position"]) for i in state["items"]}
                # Live server treats shelf cells (item positions) as blocked movement cells.
                wall_set |= shelf_set
                drop_cache.update(_build_drop(tuple(state["drop_off"]),wall_set,W,H))
                print(f"  Map: {W}×{H}  drop_off={state['drop_off']}  "
                      f"items={len(state['items'])}  walls={len(wall_set)}")
                print(f"  Item positions: { {i['type']:i['position'] for i in state['items']} }")
                print(f"  Bot start: {[b['position'] for b in state['bots']]}")
                # Draw ASCII map
                rows=[]
                for y in range(H):
                    row=""
                    for x in range(W):
                        if (x,y) in grid_wall_set: row+="W"
                        elif [x,y]==state["drop_off"]: row+="D"
                        elif any(i["position"]==[x,y] for i in state["items"]): row+="i"
                        elif any(b["position"]==[x,y] for b in state["bots"]): row+="B"
                        else: row+="."
                    rows.append(row)
                print("  "+"\n  ".join(rows))

            active  = next((o for o in state["orders"] if o["status"]=="active"),  None)
            preview = next((o for o in state["orders"] if o["status"]=="preview"), None)
            needed_active  = list(_needed_types(active))
            needed_preview = list(_needed_types(preview)) if preview else []

            for item in state["items"]:
                if item["id"] not in approach_cache:
                    approach_cache[item["id"]] = precompute_item_approach(
                        tuple(item["position"]), wall_set, W, H)

            actions = []
            action_log = []
            drop_pos = tuple(state["drop_off"])
            occupied_now = {tuple(b["position"]) for b in state["bots"]}

            for bot in state["bots"]:
                bx,by=bot["position"]; bpos=(bx,by)
                inv=bot["inventory"]
                needed_set=set(needed_active)
                bot_id = bot["id"]

                hist = stuck_history.setdefault(bot_id, [])
                hist.append(bpos)
                if len(hist) > 6:
                    hist.pop(0)
                is_stuck = len(hist) >= 4 and len(set(hist[-4:])) == 1

                # ── Explicit drop_off: server requires this action, not passive ──
                if bpos == drop_pos and inv:
                    astr = "drop_off"
                    ad   = {"bot": bot["id"], "action": "drop_off"}
                    action_log.append(f"b{bot['id']}@{bpos} inv={inv} →drop_off")
                    actions.append(ad)
                    continue

                # ── Primary policy: trained neural policy ────────────────────────
                obs = _bot_obs(bot, needed_active, needed_preview, state)
                ot = torch.tensor(obs, dtype=torch.float32, device=trainer.device)
                with torch.no_grad():
                    logits, _ = trainer.net(ot)
                    probs = torch.softmax(logits, dim=-1)
                    conf, a = torch.max(probs, dim=-1)
                proposed = ACT_STRS[a.item()]
                net_conf = float(conf.item())

                if is_stuck:
                    stuck_counts[bot_id] = stuck_counts.get(bot_id, 0) + 1
                valid_model_action = _is_valid_action(
                    bot, proposed, needed_active, needed_preview, occupied_now
                )
                use_net = (
                    valid_model_action
                    and not is_stuck
                    and net_conf >= HP["live_net_confidence"]
                )

                if use_net:
                    ad = {"bot": bot["id"], "action": proposed}
                    action_log.append(
                        f"b{bot['id']}@{bpos} inv={inv} →{proposed}(net {net_conf:.2f})"
                    )
                    actions.append(ad)
                    if proposed.startswith("move_"):
                        dx, dy = {
                            "move_up": (0, -1), "move_down": (0, 1),
                            "move_left": (-1, 0), "move_right": (1, 0),
                        }[proposed]
                        occupied_now.discard((bx, by))
                        occupied_now.add((bx + dx, by + dy))
                    continue

                # ── Batched guided BFS policy ────────────────────────────────────
                remaining_active = list(needed_active)
                for i in inv:
                    if i in remaining_active: remaining_active.remove(i)
                carrying_active = [i for i in inv if i in needed_set]

                # Deliver if: full inventory, OR have needed items and nothing left to pick
                should_deliver = (
                    len(inv) >= MAX_INVENTORY
                    or (bool(carrying_active) and not remaining_active)
                )

                # Also deliver if inventory full of wrong items (dump and retry)
                if len(inv) >= MAX_INVENTORY and not carrying_active:
                    should_deliver = True  # dump useless items at drop-off

                if should_deliver and inv:
                    e = drop_cache.get(bpos)
                    if e:
                        nc = e[0]
                        dx,dy = nc[0]-bx, nc[1]-by
                        mv = {(0,-1):"move_up",(0,1):"move_down",(-1,0):"move_left",(1,0):"move_right"}.get((dx,dy),"wait")
                        ad = {"bot": bot["id"], "action": mv}
                        action_log.append(f"b{bot['id']}@{bpos} inv={inv} →{mv}(guided:drop)")
                        actions.append(ad)
                        if mv.startswith("move_"):
                            occupied_now.discard((bx, by))
                            occupied_now.add((nc[0], nc[1]))
                        continue

                # Pick up: find nearest needed item
                target_types = set(remaining_active) or set(needed_preview)
                best_d, best_item, best_nc = 9999, None, None
                for item in state["items"]:
                    if item["type"] not in target_types: continue
                    e = approach_cache.get(item["id"], {}).get(bpos)
                    if e and e[1] < best_d:
                        best_d, best_item, best_nc = e[1], item, e[0]

                if best_item is not None:
                    if best_d == 0:  # adjacent — pick up
                        ad = {"bot": bot["id"], "action": "pick_up", "item_id": best_item["id"]}
                        action_log.append(f"b{bot['id']}@{bpos} inv={inv} →pick_up({best_item['type']},guided)")
                    else:
                        dx,dy = best_nc[0]-bx, best_nc[1]-by
                        mv = {(0,-1):"move_up",(0,1):"move_down",(-1,0):"move_left",(1,0):"move_right"}.get((dx,dy),"wait")
                        ad = {"bot": bot["id"], "action": mv}
                        action_log.append(f"b{bot['id']}@{bpos} inv={inv} →{mv}(guided→{best_item['type']})")
                    actions.append(ad)
                    if ad["action"].startswith("move_"):
                        occupied_now.discard((bx, by))
                        occupied_now.add((best_nc[0], best_nc[1]))
                    continue

                # Nothing to do — deliver what we have or wait
                if inv:
                    e = drop_cache.get(bpos)
                    if e:
                        nc = e[0]; dx,dy = nc[0]-bx, nc[1]-by
                        mv = {(0,-1):"move_up",(0,1):"move_down",(-1,0):"move_left",(1,0):"move_right"}.get((dx,dy),"wait")
                        ad = {"bot": bot["id"], "action": mv}
                        action_log.append(f"b{bot['id']}@{bpos} inv={inv} →{mv}(guided→drop)")
                        actions.append(ad)
                        if mv.startswith("move_"):
                            occupied_now.discard((bx, by))
                            occupied_now.add((nc[0], nc[1]))
                        continue

                # Last resort: bot has no valid path from current pos (e.g. adjacent to walls
                # on all BFS-reachable sides). Try moving toward drop-off or random escape.
                e = drop_cache.get(bpos)
                if e:
                    nc = e[0]; dx,dy = nc[0]-bx, nc[1]-by
                    mv = {(0,-1):"move_up",(0,1):"move_down",(-1,0):"move_left",(1,0):"move_right"}.get((dx,dy),"wait")
                else:
                    # No path at all — try all 4 directions as escape
                    import random as _r
                    mv = _r.choice(["move_up","move_down","move_left","move_right"])
                ad = {"bot": bot["id"], "action": mv}
                action_log.append(f"b{bot['id']}@{bpos} inv={inv} →{mv}(escape)")
                actions.append(ad)

            elapsed_ms = (_time.perf_counter() - t0) * 1000
            round_times.append(elapsed_ms)

            scored  = score > prev_score
            is_slow = elapsed_ms > 500
            if rnd < 5 or rnd % 20 == 0 or scored or is_slow:
                flag = f"  ⚠ {elapsed_ms:.0f}ms" if is_slow else f"  {elapsed_ms:.0f}ms"
                sflag = f"  ★+{score-prev_score} score={score}" if scored else ""
                order_str = f"need={needed_active}" if needed_active else "waiting"
                print(f"r{rnd:3d}  {order_str}  {' | '.join(action_log)}{flag}{sflag}")
            prev_score = score

            await ws.send(json.dumps({"actions":actions}))


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Grocery Bot — IL + PPO")
    p.add_argument("--difficulty",   default="easy",
                   choices=["easy","medium","hard","expert"])
    p.add_argument("--il-episodes",  type=int, default=300)
    p.add_argument("--ppo-episodes", type=int, default=500)
    p.add_argument("--il-only",      action="store_true")
    p.add_argument("--ppo-only",     action="store_true")
    p.add_argument("--curriculum",   action="store_true")
    p.add_argument("--load",         default=None)
    p.add_argument("--checkpoints",  default="checkpoints")
    p.add_argument("--device",       default="cpu")
    p.add_argument("--map-source",   default="hardcoded", choices=["hardcoded", "synthetic"],
                   help="Use fixed leaderboard-style maps or procedurally generated maps.")
    p.add_argument("--run",          action="store_true")
    p.add_argument("--url",          default=None,  help="Full WebSocket URL (wss://game.ainm.no/ws?token=...)")
    args = p.parse_args()

    if args.run:
        trainer = Trainer(
            difficulty=args.difficulty,
            device=args.device,
            map_source=args.map_source,
        )
        if args.load: trainer.load(args.load)
        if not args.url: print("--url required for --run"); return
        asyncio.run(run_live(args.url, trainer))
        return

    levels    = (["easy","medium","hard","expert"] if args.curriculum
                 else [args.difficulty])
    start_net = None

    for level in levels:
        print(f"\n{'='*60}\n  {level.upper()}\n{'='*60}")
        trainer = Trainer(
            difficulty=level,
            device=args.device,
            map_source=args.map_source,
        )
        print(f"  map_source={args.map_source}")
        print("  shelf/item cells blocked (fixed)")
        if start_net is not None:
            trainer.net.load_state_dict(start_net)
            print("  Weights transferred.")
        elif args.load:
            trainer.load(args.load)

        if not args.ppo_only:
            trainer.imitation_learning(args.il_episodes, args.checkpoints)
        if not args.il_only:
            trainer.ppo_finetune(args.ppo_episodes, args.checkpoints)

        start_net = trainer.net.state_dict()


if __name__ == "__main__":
    main()
