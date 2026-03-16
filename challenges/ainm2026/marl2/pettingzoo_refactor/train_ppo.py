from __future__ import annotations

import argparse
import collections
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical

from grocery_parallel_env import GroceryParallelEnv


@dataclass
class AgentBuffer:
    obs: list[np.ndarray] = field(default_factory=list)
    acts: list[int] = field(default_factory=list)
    masks: list[np.ndarray] = field(default_factory=list)
    logps: list[float] = field(default_factory=list)
    vals: list[float] = field(default_factory=list)
    rews: list[float] = field(default_factory=list)
    dones: list[bool] = field(default_factory=list)


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
        )
        self.actor = nn.Linear(256, n_actions)
        self.critic = nn.Linear(256, 1)

    def forward(self, x: torch.Tensor):
        h = self.trunk(x)
        return self.actor(h), self.critic(h).squeeze(-1)


def imitation_pretrain(
    net: ActorCritic,
    device: torch.device,
    difficulty: str,
    il_episodes: int,
    il_epochs: int,
    il_batch_size: int,
    seed_base: int = 200_000,
):
    if il_episodes <= 0:
        return
    from simulator import GroceryEnv
    from marl_agent import run_guided_episode

    env = GroceryEnv(difficulty=difficulty, map_source="hardcoded")
    all_obs: list[np.ndarray] = []
    all_acts: list[int] = []
    scores: list[float] = []

    print(f"IL warm-start: collecting {il_episodes} guided episodes...")
    for ep in range(il_episodes):
        obs, acts, score = run_guided_episode(env, seed=seed_base + ep)
        all_obs.extend(obs)
        all_acts.extend(acts)
        scores.append(score)
        if (ep + 1) % max(1, il_episodes // 4) == 0 or (ep + 1) == il_episodes:
            print(f"  collected {ep+1}/{il_episodes} score={score:.1f}")

    ac = collections.Counter(all_acts)
    n = len(all_acts)
    print("  IL action distribution:", {k: round(100.0 * ac[k] / max(1, n), 1) for k in range(7)})

    obs_t = torch.tensor(np.asarray(all_obs, dtype=np.float32), dtype=torch.float32, device=device)
    acts_t = torch.tensor(np.asarray(all_acts, dtype=np.int64), dtype=torch.long, device=device)

    opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    for e in range(1, il_epochs + 1):
        idx = torch.randperm(obs_t.shape[0], device=device)
        total, nb = 0.0, 0
        for start in range(0, obs_t.shape[0], il_batch_size):
            mb = idx[start:start + il_batch_size]
            logits, _ = net(obs_t[mb])
            loss = F.cross_entropy(logits, acts_t[mb])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 0.5)
            opt.step()
            total += float(loss.item())
            nb += 1
        print(f"  IL epoch {e}/{il_epochs} loss={total/max(1,nb):.4f}")

    print(f"IL warm-start complete. guided_avg={float(np.mean(scores)):.2f}")


def compute_gae(rews: list[float], vals: list[float], dones: list[bool], gamma: float, lam: float):
    adv = np.zeros(len(rews), dtype=np.float32)
    last = 0.0
    for t in reversed(range(len(rews))):
        next_v = 0.0 if (t == len(rews) - 1 or dones[t]) else vals[t + 1]
        mask = 0.0 if dones[t] else 1.0
        delta = rews[t] + gamma * next_v * mask - vals[t]
        last = delta + gamma * lam * mask * last
        adv[t] = last
    ret = adv + np.asarray(vals, dtype=np.float32)
    return adv, ret


def _needed_types(order: dict | None) -> list[str]:
    if not order:
        return []
    needed = list(order["items_required"])
    for d in order["items_delivered"]:
        if d in needed:
            needed.remove(d)
    return needed


def compute_action_masks(env: GroceryParallelEnv, agent_order: list[str]) -> np.ndarray:
    state = env.sim.get_state_dict()
    W = state["grid"]["width"]
    H = state["grid"]["height"]
    wall_set = set(map(tuple, state["grid"]["walls"])) | {tuple(i["position"]) for i in state["items"]}
    drop = tuple(state["drop_off"])
    active = next((o for o in state["orders"] if o["status"] == "active"), None)
    preview = next((o for o in state["orders"] if o["status"] == "preview"), None)
    needed = set(_needed_types(active)) | set(_needed_types(preview))

    occupied_counts: dict[tuple[int, int], int] = {}
    for b in state["bots"]:
        p = tuple(b["position"])
        occupied_counts[p] = occupied_counts.get(p, 0) + 1

    masks = np.zeros((len(agent_order), env.sim.N_ACTIONS), dtype=np.bool_)
    for i, agent in enumerate(agent_order):
        bot_idx = int(agent.split("_")[1])
        bot = state["bots"][bot_idx]
        bx, by = bot["position"]
        inv = bot["inventory"]
        valid = set()

        for ai, (dx, dy) in enumerate([(0, -1), (0, 1), (-1, 0), (1, 0)]):
            nx, ny = bx + dx, by + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            if (nx, ny) in wall_set:
                continue
            if occupied_counts.get((nx, ny), 0) > 0:
                continue
            valid.add(ai)

        if len(inv) < 3 and needed:
            for item in state["items"]:
                ix, iy = item["position"]
                if abs(ix - bx) + abs(iy - by) == 1 and item["type"] in needed:
                    valid.add(4)
                    break

        if tuple(bot["position"]) == drop and inv:
            valid.add(5)

        if not valid:
            valid.add(6)

        for a in valid:
            masks[i, a] = True

    return masks


def rollout_episode(env: GroceryParallelEnv, net: ActorCritic, device: torch.device, seed: int):
    obs, _ = env.reset(seed=seed)
    buffers = {a: AgentBuffer() for a in env.possible_agents}
    final_score = 0.0

    while env.agents:
        agent_order = [a for a in env.possible_agents if a in obs]
        action_masks = compute_action_masks(env, agent_order)
        obs_batch = torch.tensor(np.stack([obs[a] for a in agent_order]), dtype=torch.float32, device=device)
        mask_batch = torch.tensor(action_masks, dtype=torch.bool, device=device)
        with torch.no_grad():
            logits, vals = net(obs_batch)
            masked_logits = logits.masked_fill(~mask_batch, -1e9)
            dist = Categorical(logits=masked_logits)
            acts_t = dist.sample()
            logps_t = dist.log_prob(acts_t)

        actions = {a: int(acts_t[i].item()) for i, a in enumerate(agent_order)}
        next_obs, rewards, terms, truncs, infos = env.step(actions)

        for i, a in enumerate(agent_order):
            done = bool(terms[a] or truncs[a])
            buf = buffers[a]
            buf.obs.append(obs[a])
            buf.acts.append(actions[a])
            buf.masks.append(action_masks[i].astype(np.bool_))
            buf.logps.append(float(logps_t[i].item()))
            buf.vals.append(float(vals[i].item()))
            buf.rews.append(float(rewards[a]))
            buf.dones.append(done)
            final_score = float(infos[a].get("score", final_score))

        obs = next_obs

    return buffers, final_score


def build_train_tensors(buffers: dict[str, AgentBuffer], gamma: float, lam: float, device: torch.device):
    obs_all, act_all, mask_all, logp_all, adv_all, ret_all, val_all = [], [], [], [], [], [], []
    for _, b in buffers.items():
        if not b.rews:
            continue
        adv, ret = compute_gae(b.rews, b.vals, b.dones, gamma, lam)
        obs_all.append(np.asarray(b.obs, dtype=np.float32))
        act_all.append(np.asarray(b.acts, dtype=np.int64))
        mask_all.append(np.asarray(b.masks, dtype=np.bool_))
        logp_all.append(np.asarray(b.logps, dtype=np.float32))
        adv_all.append(adv)
        ret_all.append(ret)
        val_all.append(np.asarray(b.vals, dtype=np.float32))

    obs = torch.tensor(np.concatenate(obs_all), dtype=torch.float32, device=device)
    acts = torch.tensor(np.concatenate(act_all), dtype=torch.long, device=device)
    masks = torch.tensor(np.concatenate(mask_all), dtype=torch.bool, device=device)
    old_logps = torch.tensor(np.concatenate(logp_all), dtype=torch.float32, device=device)
    advs = torch.tensor(np.concatenate(adv_all), dtype=torch.float32, device=device)
    rets = torch.tensor(np.concatenate(ret_all), dtype=torch.float32, device=device)
    old_vals = torch.tensor(np.concatenate(val_all), dtype=torch.float32, device=device)

    advs = (advs - advs.mean()) / (advs.std() + 1e-8)
    return obs, acts, masks, old_logps, advs, rets, old_vals


def ppo_update(net: ActorCritic, opt: torch.optim.Optimizer, batch, ppo_epochs=4, batch_size=4096, clip=0.2, entropy_coef=0.01):
    obs, acts, masks, old_logps, advs, rets, old_vals = batch
    n = obs.shape[0]

    stats = {"pi": 0.0, "v": 0.0, "h": 0.0}
    updates = 0

    for _ in range(ppo_epochs):
        idx = torch.randperm(n, device=obs.device)
        for start in range(0, n, batch_size):
            mb = idx[start:start + batch_size]
            logits, vals = net(obs[mb])
            masked_logits = logits.masked_fill(~masks[mb], -1e9)
            dist = Categorical(logits=masked_logits)
            new_logps = dist.log_prob(acts[mb])
            entropy = dist.entropy().mean()

            ratio = (new_logps - old_logps[mb]).exp()
            s1 = ratio * advs[mb]
            s2 = ratio.clamp(1 - clip, 1 + clip) * advs[mb]
            pi_loss = -torch.min(s1, s2).mean()

            v_clipped = old_vals[mb] + (vals - old_vals[mb]).clamp(-clip, clip)
            v_loss = torch.max(F.mse_loss(vals, rets[mb]), F.mse_loss(v_clipped, rets[mb]))

            loss = pi_loss + 0.5 * v_loss - entropy_coef * entropy
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 0.5)
            opt.step()

            stats["pi"] += float(pi_loss.item())
            stats["v"] += float(v_loss.item())
            stats["h"] += float(entropy.item())
            updates += 1

    if updates:
        for k in stats:
            stats[k] /= updates
    return stats


def evaluate(env: GroceryParallelEnv, net: ActorCritic, device: torch.device, episodes: int = 10, seed_base: int = 100_000):
    scores = []
    for ep in range(episodes):
        obs, _ = env.reset(seed=seed_base + ep)
        score = 0.0
        while env.agents:
            agent_order = [a for a in env.possible_agents if a in obs]
            action_masks = compute_action_masks(env, agent_order)
            obs_batch = torch.tensor(np.stack([obs[a] for a in agent_order]), dtype=torch.float32, device=device)
            mask_batch = torch.tensor(action_masks, dtype=torch.bool, device=device)
            with torch.no_grad():
                logits, _ = net(obs_batch)
                masked_logits = logits.masked_fill(~mask_batch, -1e9)
                acts = torch.argmax(masked_logits, dim=-1)
            actions = {a: int(acts[i].item()) for i, a in enumerate(agent_order)}
            obs, _, _, _, infos = env.step(actions)
            if agent_order:
                score = float(infos[agent_order[0]].get("score", score))
        scores.append(score)
    return float(np.mean(scores)), float(np.max(scores))


def main():
    p = argparse.ArgumentParser(description="PettingZoo PPO baseline")
    p.add_argument("--difficulty", default="easy", choices=["easy", "medium", "hard", "expert"])
    p.add_argument("--episodes", type=int, default=300)
    p.add_argument("--device", default="cpu")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--eval-every", type=int, default=20)
    p.add_argument("--rollouts-per-update", type=int, default=8)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--ppo-epochs", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=4096)
    p.add_argument("--entropy-coef", type=float, default=0.01)
    p.add_argument("--il-episodes", type=int, default=0)
    p.add_argument("--il-epochs", type=int, default=5)
    p.add_argument("--il-batch-size", type=int, default=4096)
    p.add_argument("--eval-only", action="store_true")
    p.add_argument("--load", default=None)
    args = p.parse_args()

    ckpt_dir = Path("pettingzoo_refactor/checkpoints")
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    env = GroceryParallelEnv(difficulty=args.difficulty)
    obs_dim = int(env.observation_space(env.possible_agents[0]).shape[0])
    n_actions = int(env.action_space(env.possible_agents[0]).n)

    device = torch.device(args.device)
    net = ActorCritic(obs_dim, n_actions).to(device)
    opt = torch.optim.Adam(net.parameters(), lr=args.lr)

    if args.load:
        net.load_state_dict(torch.load(args.load, map_location=device))

    if args.eval_only:
        avg, best = evaluate(env, net, device, episodes=20)
        print(f"eval avg={avg:.2f} best={best:.2f}")
        return

    imitation_pretrain(
        net=net,
        device=device,
        difficulty=args.difficulty,
        il_episodes=args.il_episodes,
        il_epochs=args.il_epochs,
        il_batch_size=args.il_batch_size,
        seed_base=args.seed * 1000,
    )

    scores: list[float] = []
    best_eval = float("-inf")

    ep = 1
    while ep <= args.episodes:
        chunk_end = min(ep + args.rollouts_per_update - 1, args.episodes)
        merged = {a: AgentBuffer() for a in env.possible_agents}
        chunk_scores = []
        for epi in range(ep, chunk_end + 1):
            buffers, score = rollout_episode(env, net, device, seed=args.seed + epi)
            chunk_scores.append(score)
            scores.append(score)
            for a in env.possible_agents:
                b = buffers[a]
                m = merged[a]
                m.obs.extend(b.obs)
                m.acts.extend(b.acts)
                m.masks.extend(b.masks)
                m.logps.extend(b.logps)
                m.vals.extend(b.vals)
                m.rews.extend(b.rews)
                m.dones.extend(b.dones)

        batch = build_train_tensors(merged, gamma=0.99, lam=0.95, device=device)
        stats = ppo_update(
            net, opt, batch,
            ppo_epochs=args.ppo_epochs,
            batch_size=args.batch_size,
            entropy_coef=args.entropy_coef,
        )

        avg20 = float(np.mean(scores[-20:]))
        print(
            f"ep {chunk_end:4d}/{args.episodes} batch_avg={float(np.mean(chunk_scores)):5.1f} avg20={avg20:5.1f} "
            f"pi={stats['pi']:+.3f} v={stats['v']:.3f} H={stats['h']:.3f}"
        )

        if chunk_end % args.eval_every == 0 or chunk_end == args.episodes:
            eval_avg, eval_best = evaluate(env, net, device, episodes=10)
            print(f"  eval avg={eval_avg:.2f} best={eval_best:.2f}")
            if eval_avg > best_eval:
                best_eval = eval_avg
                torch.save(net.state_dict(), ckpt_dir / f"{args.difficulty}_best.pt")
        ep = chunk_end + 1

    torch.save(net.state_dict(), ckpt_dir / f"{args.difficulty}_ep{args.episodes}.pt")
    print(f"done best_eval={best_eval:.2f}")


if __name__ == "__main__":
    main()
