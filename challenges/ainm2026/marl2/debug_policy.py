"""
debug_policy.py — Inspect trained policy behaviour from a checkpoint.

Usage
─────
  python debug_policy.py --load checkpoints/easy_best.pt --difficulty easy
  python debug_policy.py --load checkpoints/easy_best.pt --seeds 1 2 3 4 5
  python debug_policy.py --load checkpoints/easy_best.pt --compare   # vs guided
  python debug_policy.py --load checkpoints/easy_best.pt --trace 2   # step-by-step seed 2

Outputs
───────
  • Per-episode score, return, and episode length
  • Action distribution (what does the policy actually do?)
  • Entropy per step (is the policy confident or uncertain?)
  • Value estimates vs actual returns (is the critic calibrated?)
  • Mistake analysis: steps where policy diverges from guided policy
  • Stall detection: bot stuck in the same cell for many steps
"""

from __future__ import annotations

import argparse
import collections
import random

# ── Graceful torch import ────────────────────────────────────────────────────
try:
    import torch
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from simulator import GroceryEnv, _needed_types, DIFFICULTY


# ── Minimal ActorCritic (mirrors marl_agent.py, no import needed) ────────────
if HAS_TORCH:
    import torch.nn as nn

    class ActorCritic(nn.Module):
        def __init__(self, obs_dim=24, n_actions=7, hidden=128):
            super().__init__()
            self.trunk = nn.Sequential(
                nn.Linear(obs_dim, hidden), nn.LayerNorm(hidden), nn.ReLU(),
                nn.Linear(hidden, hidden), nn.ReLU(),
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

        def action_probs(self, obs):
            logits, value = self(obs)
            return F.softmax(logits, dim=-1), value


# ── Guided reference policy (BFS oracle) ─────────────────────────────────────

def guided_action(bot_idx: int, env: GroceryEnv) -> int:
    state      = env.get_state_dict()
    bot        = state["bots"][bot_idx]
    bx, by     = bot["position"]; bpos = (bx, by)
    drop       = state["drop_off"]
    active     = next((o for o in state["orders"] if o["status"] == "active"), None)
    needed_set = set(_needed_types(active))
    carrying   = [i for i in bot["inventory"] if i in needed_set]
    if carrying and [bx, by] == drop:
        return random.choice([0, 1, 2, 3])
    if carrying or len(bot["inventory"]) >= 3:
        e = env._drop_cache.get(bpos)
        if e: return {(0,-1):0,(0,1):1,(-1,0):2,(1,0):3}.get((e[0][0]-bx,e[0][1]-by), 6)
    best_d, best_nc = 9999, None
    for item in state["items"]:
        if item["type"] not in needed_set: continue
        e = env._approach_cache.get(item["id"], {}).get(bpos)
        if e and e[1] < best_d: best_d, best_nc = e[1], e[0]
    if best_nc:
        if best_d == 0: return 4
        return {(0,-1):0,(0,1):1,(-1,0):2,(1,0):3}.get(
            (best_nc[0]-bx, best_nc[1]-by), random.randint(0, 3))
    if bot["inventory"]:
        e = env._drop_cache.get(bpos)
        if e: return {(0,-1):0,(0,1):1,(-1,0):2,(1,0):3}.get((e[0][0]-bx,e[0][1]-by), 6)
    return random.randint(0, 3)


# ── Core episode runner ───────────────────────────────────────────────────────

NAMES = GroceryEnv.ACTION_NAMES  # move_up … wait

def run_episode(net, env: GroceryEnv, seed: int, deterministic: bool = True):
    """
    Run one episode with the loaded network.
    Returns dict with per-step diagnostics.
    """
    env.seed = seed
    obs_list = env.reset()
    n_bots   = env.n_bots

    steps = []
    done  = False

    while not done:
        state    = env.get_state_dict()
        obs_snap = list(obs_list)

        # Network decisions
        net_actions, entropies, values, probs_list = [], [], [], []
        for obs in obs_snap:
            if HAS_TORCH:
                ot = torch.tensor(obs, dtype=torch.float32)
                with torch.no_grad():
                    probs, val = net.action_probs(ot)
                    a, _, ent, _ = net.act(ot, deterministic=deterministic)
                net_actions.append(a.item())
                entropies.append(ent.item() if HAS_TORCH else 0.0)
                values.append(val.item())
                probs_list.append(probs.tolist())
            else:
                net_actions.append(random.randint(0, 6))
                entropies.append(0.0)
                values.append(0.0)
                probs_list.append([1/7]*7)

        # Guided reference
        guided_acts = [guided_action(i, env) for i in range(n_bots)]

        obs_list, reward, done, info = env.step(net_actions)

        steps.append({
            "round":       state["round"],
            "net_actions": net_actions,
            "guided_acts": guided_acts,
            "entropies":   entropies,
            "values":      values,
            "probs":       probs_list,
            "reward":      reward,
            "score":       info["score"],
            "bots":        [{"pos": tuple(b["position"]), "inv": list(b["inventory"])}
                            for b in state["bots"]],
            "active_needed": _needed_types(
                next((o for o in state["orders"] if o["status"] == "active"), None)
            ),
        })

    return steps


# ── Diagnostic functions ──────────────────────────────────────────────────────

def action_distribution(steps):
    counts = collections.Counter()
    for s in steps:
        for a in s["net_actions"]:
            counts[a] += 1
    total = sum(counts.values())
    return {NAMES[a]: f"{100*c/total:.1f}%" for a, c in sorted(counts.items())}


def divergence_from_guided(steps):
    """Steps where policy disagrees with guided oracle."""
    mismatches = []
    for s in steps:
        for i, (net_a, guide_a) in enumerate(zip(s["net_actions"], s["guided_acts"])):
            if net_a != guide_a:
                mismatches.append({
                    "round":    s["round"],
                    "bot":      i,
                    "pos":      s["bots"][i]["pos"],
                    "inv":      s["bots"][i]["inv"],
                    "needed":   s["active_needed"],
                    "net":      NAMES[net_a],
                    "guided":   NAMES[guide_a],
                    "entropy":  s["entropies"][i],
                    "probs":    {NAMES[a]: f"{p:.2f}" for a, p in enumerate(s["probs"][i])},
                })
    return mismatches


def stall_detection(steps, threshold=10):
    """Bots that stay in the same position for ≥ threshold consecutive steps."""
    n_bots   = len(steps[0]["bots"])
    stalls   = []
    for bot_i in range(n_bots):
        streak_pos   = steps[0]["bots"][bot_i]["pos"]
        streak_start = 0
        streak_len   = 1
        for t, s in enumerate(steps[1:], 1):
            pos = s["bots"][bot_i]["pos"]
            if pos == streak_pos:
                streak_len += 1
                if streak_len == threshold:
                    stalls.append({
                        "bot": bot_i, "pos": streak_pos,
                        "start": streak_start, "length": streak_len,
                    })
            else:
                streak_pos   = pos
                streak_start = t
                streak_len   = 1
    return stalls


def value_calibration(steps, gamma=0.99):
    """Compare predicted V(s_t) with actual discounted return G_t."""
    T       = len(steps)
    returns = [0.0] * T
    G = 0.0
    for t in reversed(range(T)):
        G = steps[t]["reward"] + gamma * G
        returns[t] = G

    errors = []
    for t, (s, G_t) in enumerate(zip(steps, returns)):
        for v in s["values"]:
            errors.append(abs(v - G_t))

    if not errors:
        return {"mae": 0, "max_err": 0}
    return {
        "mae":     sum(errors) / len(errors),
        "max_err": max(errors),
        "G_0":     returns[0],
        "V_0":     steps[0]["values"][0] if steps[0]["values"] else 0,
    }


def entropy_profile(steps):
    """Average entropy by thirds of the episode — shows if policy collapses mid-game."""
    T = len(steps)
    thirds = [steps[:T//3], steps[T//3:2*T//3], steps[2*T//3:]]
    labels = ["early", "mid", "late"]
    result = {}
    for label, segment in zip(labels, thirds):
        all_ents = [e for s in segment for e in s["entropies"]]
        result[label] = sum(all_ents) / max(len(all_ents), 1)
    return result


# ── Report printers ───────────────────────────────────────────────────────────

def print_summary(steps, seed, label="policy"):
    score  = steps[-1]["score"]
    G      = sum(s["reward"] for s in steps)
    G_disc = sum((0.99**t) * s["reward"] for t, s in enumerate(steps))
    div    = divergence_from_guided(steps)
    stalls = stall_detection(steps)
    cal    = value_calibration(steps)
    ent    = entropy_profile(steps)
    adist  = action_distribution(steps)

    print(f"\n{'─'*58}")
    print(f"  Seed {seed}  |  {label}")
    print(f"{'─'*58}")
    print(f"  Score:        {score}")
    print(f"  G (γ=1):      {G:.1f}   G (γ=0.99): {G_disc:.1f}")
    print(f"  Steps:        {len(steps)}")
    print(f"  Action dist:  {adist}")
    print(f"  Entropy:      early={ent['early']:.3f}  mid={ent['mid']:.3f}  late={ent['late']:.3f}")
    if HAS_TORCH:
        print(f"  Value:        V(s0)={cal.get('V_0',0):.2f}  G_0={cal.get('G_0',0):.2f}  "
              f"MAE={cal.get('mae',0):.2f}  max_err={cal.get('max_err',0):.2f}")
    print(f"  Divergences from guided: {len(div)}/{len(steps)} steps "
          f"({100*len(div)/max(len(steps),1):.1f}%)")
    if stalls:
        for st in stalls:
            print(f"  ⚠ Bot {st['bot']} stalled at {st['pos']} "
                  f"for {st['length']} steps from round {st['start']}")


def print_trace(steps, max_steps=50):
    """Print step-by-step trace of the first max_steps rounds."""
    print(f"\n{'─'*80}")
    print(f"  STEP-BY-STEP TRACE (first {max_steps} rounds)")
    print(f"{'─'*80}")
    print(f"  {'rnd':>3}  {'bot':>3}  {'pos':>8}  {'inv':>12}  {'needed':>16}  "
          f"{'net':>10}  {'guided':>10}  {'match':>5}  {'H':>5}  {'V':>6}")
    print(f"  {'---':>3}  {'---':>3}  {'---':>8}  {'---':>12}  {'------':>16}  "
          f"{'---':>10}  {'------':>10}  {'-----':>5}  {'-':>5}  {'-':>6}")

    for s in steps[:max_steps]:
        for i in range(len(s["bots"])):
            bot     = s["bots"][i]
            net_a   = NAMES[s["net_actions"][i]]
            guide_a = NAMES[s["guided_acts"][i]]
            match   = "✓" if s["net_actions"][i] == s["guided_acts"][i] else "✗"
            H       = s["entropies"][i] if i < len(s["entropies"]) else 0
            V       = s["values"][i]    if i < len(s["values"])    else 0
            needed  = ",".join(s["active_needed"][:2]) + ("…" if len(s["active_needed"]) > 2 else "")
            inv_str = ",".join(bot["inv"]) if bot["inv"] else "—"
            print(f"  {s['round']:>3}  {i:>3}  {str(bot['pos']):>8}  "
                  f"{inv_str:>12}  {needed:>16}  "
                  f"{net_a:>10}  {guide_a:>10}  {match:>5}  "
                  f"{H:>5.2f}  {V:>6.2f}")

        if s["reward"] != 0:
            print(f"  {'':>3}  {'↑ reward':>3}  {s['reward']:+.2f}  score={s['score']}")


def print_divergence_analysis(steps, max_show=20):
    """Show the most instructive divergence cases."""
    div = divergence_from_guided(steps)
    if not div:
        print("\n  ✓ Policy matches guided on all steps.")
        return

    print(f"\n  DIVERGENCE ANALYSIS ({len(div)} mismatches)")
    print(f"  {'rnd':>4}  {'bot':>3}  {'pos':>8}  {'inv':>10}  "
          f"{'needed':>14}  {'net':>10}  {'guided':>10}  {'H':>5}")

    # Group by (net_action, guided_action) to find systematic errors
    pattern_counts = collections.Counter(
        (d["net"], d["guided"]) for d in div
    )
    print("\n  Top divergence patterns:")
    for (net, guided), count in pattern_counts.most_common(5):
        print(f"    policy={net:12s}  oracle={guided:12s}  × {count}")

    print(f"\n  Sample mismatches (first {min(max_show, len(div))}):")
    for d in div[:max_show]:
        print(f"  r={d['round']:>4}  b={d['bot']}  {str(d['pos']):>8}  "
              f"inv={str(d['inv']):>10}  need={str(d['needed'][:2]):>14}  "
              f"net={d['net']:>10}  oracle={d['guided']:>10}  H={d['entropy']:.2f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def load_net(checkpoint_path: str) -> "ActorCritic | None":
    if not HAS_TORCH:
        print("WARNING: torch not available — running without network (guided policy only)")
        return None
    ckpt = torch.load(checkpoint_path, map_location="cpu")
    net  = ActorCritic()
    net.load_state_dict(ckpt["net"])
    net.eval()
    difficulty = ckpt.get("difficulty", "?")
    best_score = ckpt.get("best_score", "?")
    scores     = ckpt.get("scores", [])
    print(f"Loaded '{checkpoint_path}'")
    print(f"  difficulty={difficulty}  best_score={best_score}")
    if scores:
        recent = scores[-20:]
        print(f"  last 20 scores: min={min(recent)}  max={max(recent)}  "
              f"avg={sum(recent)/len(recent):.1f}")
    return net


def main():
    p = argparse.ArgumentParser(description="Debug a trained policy checkpoint")
    p.add_argument("--load",       required=True,  help="Path to .pt checkpoint")
    p.add_argument("--difficulty", default=None,   help="Override difficulty (auto-detected from ckpt)")
    p.add_argument("--seeds",      type=int, nargs="+", default=list(range(1, 11)),
                   help="Seeds to evaluate (default: 1-10)")
    p.add_argument("--compare",    action="store_true",
                   help="Compare policy vs guided oracle side-by-side")
    p.add_argument("--trace",      type=int, default=None, metavar="SEED",
                   help="Print step-by-step trace for a single seed")
    p.add_argument("--diverge",    type=int, default=None, metavar="SEED",
                   help="Show full divergence analysis for a single seed")
    p.add_argument("--deterministic", action="store_true", default=True,
                   help="Use deterministic (argmax) policy (default: True)")
    p.add_argument("--stochastic", action="store_true",
                   help="Use stochastic policy during eval")
    args = p.parse_args()

    net = load_net(args.load)

    # Auto-detect difficulty from checkpoint
    difficulty = args.difficulty
    if difficulty is None and HAS_TORCH:
        ckpt = torch.load(args.load, map_location="cpu")
        difficulty = ckpt.get("difficulty", "easy")
    difficulty = difficulty or "easy"

    deterministic = not args.stochastic
    env = GroceryEnv(difficulty=difficulty)
    print(f"\nDifficulty: {difficulty}  |  Deterministic: {deterministic}")

    # ── Trace mode ──────────────────────────────────────────────────────────
    if args.trace is not None:
        seed  = args.trace
        steps = run_episode(net, env, seed, deterministic)
        print_summary(steps, seed)
        print_trace(steps)
        return

    # ── Divergence analysis mode ─────────────────────────────────────────────
    if args.diverge is not None:
        seed  = args.diverge
        steps = run_episode(net, env, seed, deterministic)
        print_summary(steps, seed)
        print_divergence_analysis(steps)
        return

    # ── Multi-seed evaluation ────────────────────────────────────────────────
    print(f"\nEvaluating on seeds {args.seeds}…")

    policy_scores, guided_scores_list = [], []

    for seed in args.seeds:
        # Policy
        steps_policy = run_episode(net, env, seed, deterministic)
        policy_scores.append(steps_policy[-1]["score"])

        # Guided reference
        env.seed = seed; obs = env.reset(); done = False
        while not done:
            acts = [guided_action(i, env) for i in range(env.n_bots)]
            obs, _, done, info = env.step(acts)
        guided_scores_list.append(info["score"])

        if args.compare:
            print_summary(steps_policy, seed, label="policy")
            print(f"  Guided score: {info['score']}")
        else:
            div_count = len(divergence_from_guided(steps_policy))
            div_pct   = 100 * div_count / max(len(steps_policy), 1)
            stalls    = stall_detection(steps_policy)
            print(f"  seed={seed:4d}  policy={steps_policy[-1]['score']:3d}  "
                  f"guided={info['score']:3d}  "
                  f"diverge={div_pct:4.1f}%  stalls={len(stalls)}")

    # ── Aggregate summary ─────────────────────────────────────────────────────
    print(f"\n{'═'*58}")
    print(f"  AGGREGATE  ({len(args.seeds)} seeds)")
    print(f"{'═'*58}")
    print(f"  Policy scores:  "
          f"min={min(policy_scores)}  max={max(policy_scores)}  "
          f"avg={sum(policy_scores)/len(policy_scores):.1f}")
    print(f"  Guided scores:  "
          f"min={min(guided_scores_list)}  max={max(guided_scores_list)}  "
          f"avg={sum(guided_scores_list)/len(guided_scores_list):.1f}")
    delta = sum(policy_scores)/len(policy_scores) - sum(guided_scores_list)/len(guided_scores_list)
    print(f"  Policy vs guided delta: {delta:+.1f}")

    # ── Per-difficulty context ────────────────────────────────────────────────
    print("\n  Difficulty context:")
    print(f"    {DIFFICULTY[difficulty]}")


if __name__ == "__main__":
    main()
