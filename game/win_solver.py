"""Find the strategy that minimizes the probability of losing a 1v1 game.

Rules: player 1 and player 2 take turns. The game ends after the round (P1's
turn followed by P2's turn) in which someone exceeds TARGET points. The player
with the most points wins; ties are possible. Both players minimize their own
probability of losing, so a tie is as good as a win.

Losses are stored in absolute terms as (L1, L2): the probability that player 1
loses and the probability that player 2 loses. L1 + L2 + P(tie) = 1.

Tables (A = P1's score, B = P2's score, both <= TARGET):
    R[A, B]  P1 is about to start a turn (start of a round)
    T[A, B]  P2 is about to start a turn, P1 has finished at A
    F[n]     P2's final turn: P1 has exceeded TARGET and leads by n points

Each turn is solved like game/solver.py, except that the payoff of stopping
with turn score s is looked up in these tables instead of being s itself.
"""
import os
import pickle
import numpy as np
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations_with_replacement, repeat
from game.solver import possible_allocations, P, NUM_DICE

TARGET = 199  # The game ends when someone exceeds this, i.e. reaches 200
NEED_CAP = 300  # F[n] is treated as F[NEED_CAP] beyond this lead
LEAD_CAP = 150  # P1 stops rolling fresh dice when above TARGET and this far ahead

L1, L2, BUST = 0, 1, 2  # Value channels: P1 loses, P2 loses, P(this turn busts)


""" ---- Turn graph (independent of the score) ---- """

def _build_turn_graph():
    """Enumerate run configurations (r1, r2, c) and group rolls by the allocations they allow"""
    configs = {(0, 0, 0)}
    todo = [(0, 0, 0)]
    groups = defaultdict(lambda: defaultdict(float))  # cfg => allocation set => probability
    while todo:
        cfg = todo.pop()
        if sum(cfg) == NUM_DICE:  continue
        for x in combinations_with_replacement(range(1, 7), NUM_DICE - sum(cfg)):
            roll = Counter(x)
            allocs = frozenset(s[1:] for s in possible_allocations((0,) + cfg, roll))
            groups[cfg][allocs] += P(roll)
            for nxt in allocs - configs:
                configs.add(nxt)
                todo.append(nxt)

    configs = sorted(configs)
    index = {cfg: i for i, cfg in enumerate(configs)}
    bust_row = len(configs)  # Extra row in the value array that holds the bust value

    layers = []  # Ordered by dice used, from 6 down to 0
    for used in range(NUM_DICE - 1, -1, -1):
        cfgs = [cfg for cfg in configs if sum(cfg) == used]
        group_starts, probs, alloc_starts, alloc_idx = [], [], [], []
        for cfg in cfgs:
            group_starts.append(len(probs))
            for allocs, p in groups[cfg].items():
                probs.append(p)
                alloc_starts.append(len(alloc_idx))
                alloc_idx.extend(sorted(index[a] for a in allocs) or [bust_row])
        layers.append(dict(
            cfgs=np.array([index[cfg] for cfg in cfgs]),
            group_starts=np.array(group_starts),
            probs=np.array(probs)[None, :, None],
            alloc_starts=np.array(alloc_starts),
            alloc_counts=np.diff(alloc_starts + [len(alloc_idx)]),
            alloc_idx=np.array(alloc_idx),
        ))

    return dict(
        configs=configs,
        score=np.array([(r1 + 2*r2)*(c + 1) for r1, r2, c in configs]),
        full=np.array([index[cfg] for cfg in configs if sum(cfg) == NUM_DICE]),
        layers=layers,
        bust_row=bust_row,
    )

GRAPH = _build_turn_graph()


""" ---- Solving a single turn ---- """

def _best(a, b, mover):
    """Elementwise pick of a or b (shape (3, ..., batch)): lowest own loss, then highest opponent loss"""
    own, opp = mover, 1 - mover
    pick_a = (a[own] < b[own]) | ((a[own] == b[own]) & (a[opp] >= b[opp]))
    return np.where(pick_a, a, b)

def _best_per_group(values, starts, counts, mover):
    """Like _best, but over each segment of `values` (shape (3, N, batch)) along axis 1"""
    own, opp = mover, 1 - mover
    best = np.empty((3, len(starts), values.shape[2]))

    best[own] = np.minimum.reduceat(values[own], starts, axis=0)
    chosen = values[own] == np.repeat(best[own], counts, axis=0)

    best[opp] = np.maximum.reduceat(np.where(chosen, values[opp], -np.inf), starts, axis=0)
    chosen &= values[opp] == np.repeat(best[opp], counts, axis=0)

    best[BUST] = np.minimum.reduceat(np.where(chosen, values[BUST], np.inf), starts, axis=0)
    return best

def solve_turn(stop_loss, bust_loss, mover, max_bank=None, record=None):
    """Solve one turn for a batch of independent situations.

    stop_loss: (S, 2, batch) losses (L1, L2) when stopping with turn score s.
               Scores beyond S-1 count as S-1.
    bust_loss: (2, batch) losses when the turn busts
    mover:     0 if player 1 is taking this turn, 1 for player 2
    max_bank:  per column: rolling a fresh set of dice is not allowed with more
               points banked (default S-1)
    record:    optional dict; filled with (t, r1, r2, c) => (stop, play) values
               (only for a batch of one)

    Returns (3, batch): L1, L2 and the probability that the turn busts
    """
    g = GRAPH
    S, _, batch = stop_loss.shape
    score = g['score']
    full = g['full']

    # Sort columns by banking room, so the columns still being solved are a prefix
    max_bank = np.broadcast_to(S - 1 if max_bank is None else max_bank, (batch,))
    order = np.argsort(-max_bank, kind='stable')
    max_bank = max_bank[order]

    stop = np.zeros((3, S, batch))
    stop[:2] = stop_loss[:, :, order].transpose(1, 0, 2)

    # fresh[t]: value of rolling all dice with t points banked (inf: not allowed)
    fresh = np.full((3, max_bank[0] + score.max() + 1, batch), np.inf)

    values = np.zeros((3, len(g['configs']) + 1, batch))
    values[:2, g['bust_row']] = bust_loss[:, order]
    values[BUST, g['bust_row']] = 1

    for t in range(max_bank[0], -1, -1):
        k = np.searchsorted(-max_bank, -t, side='right')  # Columns with max_bank >= t
        stop_t = stop[:, np.minimum(t + score, S - 1), :k]

        # All dice used: stop, or bank the run and roll all dice again
        play_full = fresh[:, t + score[full], :k]
        values[:, full, :k] = _best(stop_t[:, full], play_full, mover)
        if record is not None:
            for j, i in enumerate(full):
                record[(t,) + g['configs'][i]] = (stop_t[:, i, 0], play_full[:, j, 0])

        for layer in g['layers']:
            gathered = values[:, layer['alloc_idx'], :k]
            per_roll = _best_per_group(gathered, layer['alloc_starts'], layer['alloc_counts'], mover)
            play = np.add.reduceat(per_roll * layer['probs'], layer['group_starts'], axis=1)

            cfgs = layer['cfgs']
            if record is not None:
                for j, i in enumerate(cfgs):
                    record[(t,) + g['configs'][i]] = (stop_t[:, i, 0], play[:, j, 0])

            if len(cfgs) == 1 and g['configs'][cfgs[0]] == (0, 0, 0):
                fresh[:, t, :k] = play[:, 0]  # Empty board: you have to roll
            else:
                values[:, cfgs, :k] = _best(stop_t[:, cfgs], play, mover)

    result = np.empty((3, batch))
    result[:, order] = fresh[:, 0]
    return result


""" ---- Payoffs of ending a turn ---- """

def final_turn_loss(n, s):
    """P2's final turn, trailing by n > 0: losses (L1, L2) when stopping with turn score s"""
    return np.stack([s > n, s < n], axis=-1).astype(float)

def p1_stop_loss(A, B, T, F):
    """(S, 2, batch) losses for P1 ending a turn at A + s"""
    S = int((B - A).max()) + NEED_CAP + 2
    a = A[None, :] + np.arange(S)[:, None]
    inside = (a <= TARGET)[..., None]
    next_turn = T[np.minimum(a, TARGET), B[None, :]]
    final = F[np.clip(a - B[None, :], 0, NEED_CAP)]
    return np.where(inside, next_turn, final).transpose(0, 2, 1)

def p1_max_bank(A, B):
    """Most points P1 may bank and still roll a fresh set: always allowed up to TARGET,
    above it only while less than LEAD_CAP ahead"""
    return np.maximum(TARGET - A, B - A + LEAD_CAP - 1)

def p2_stop_loss(A, B, R):
    """(S, 2, batch) losses for P2 ending a regular turn at B + s"""
    S = TARGET + 2 - int(B.min())
    b = B[None, :] + np.arange(S)[:, None]
    inside = (b <= TARGET)[..., None]
    next_round = R[A[None, :], np.minimum(b, TARGET)]
    p2_wins = np.array([1.0, 0.0])
    return np.where(inside, next_round, p2_wins).transpose(0, 2, 1)

def p2_max_bank(B):
    """Banking beyond TARGET wins, so there's no reason to roll a fresh set after that"""
    return TARGET - B


""" ---- Solving the game ---- """

def solve_final_turns():
    """F[n] for P2's final turn trailing by n (F[0] is unused)"""
    n = np.arange(1, NEED_CAP + 1)
    s = np.arange(NEED_CAP + 2)
    stop_loss = final_turn_loss(n[None, :], s[:, None]).transpose(0, 2, 1)
    bust_loss = np.tile([[0.0], [1.0]], (1, len(n)))
    F = np.zeros((NEED_CAP + 1, 2))
    F[1:] = solve_turn(stop_loss, bust_loss, mover=1, max_bank=n)[:2].T
    return F

def _solve_positions(p1_loss, p1_bank, p2_loss, p2_bank, x, tol, max_iter):
    """R and T for positions whose only unsolved dependency is the bust loop
    R[A, B] -> T[A, B] -> R[A, B].

    Policy iteration: with fixed policies both turns are linear in their bust
    value (value = a + p_bust * bust_value), which gives the fixed point directly.
    x is the initial guess for R.
    """
    for iteration in range(1, max_iter + 1):
        t_val = solve_turn(p2_loss, x, mover=1, max_bank=p2_bank)
        r_val = solve_turn(p1_loss, t_val[:2], mover=0, max_bank=p1_bank)
        bt, br = t_val[BUST], r_val[BUST]
        at = t_val[:2] - bt*x
        ar = r_val[:2] - br*t_val[:2]
        x_new = (ar + br*at) / (1 - br*bt)
        done = np.abs(x_new - x).max() < tol
        x = x_new
        if done:
            return x, at + bt*x, iteration
    raise RuntimeError("Policy iteration did not converge")

def solve(processes=None, tol=1e-13, max_iter=50, verbose=True):
    """Compute the tables R, T and F"""
    processes = processes or os.cpu_count()
    F = solve_final_turns()
    R = np.zeros((TARGET + 1, TARGET + 1, 2))
    T = np.zeros((TARGET + 1, TARGET + 1, 2))

    with ProcessPoolExecutor(processes) as pool:
        # Every turn that doesn't bust increases A + B, so solve from high to low A + B.
        # Positions with the same A + B don't depend on each other: solve them in parallel
        for total in range(2*TARGET, -1, -1):
            A = np.arange(max(0, total - TARGET), min(total, TARGET) + 1)
            B = total - A

            # Initial guess for R[A, B]: a neighbouring position that is already solved
            if total == 2*TARGET:
                x = np.full((2, len(A)), 0.5)
            else:
                x = np.where(A < TARGET, R[np.minimum(A + 1, TARGET), B].T, R[A, np.minimum(B + 1, TARGET)].T)

            # Interleave positions over the workers to balance their workload
            chunks = [np.arange(i, len(A), processes) for i in range(min(processes, len(A)))]
            p1_loss, p1_bank = p1_stop_loss(A, B, T, F), p1_max_bank(A, B)
            p2_loss, p2_bank = p2_stop_loss(A, B, R), p2_max_bank(B)
            results = pool.map(
                _solve_positions,
                [p1_loss[..., c] for c in chunks], [p1_bank[c] for c in chunks],
                [p2_loss[..., c] for c in chunks], [p2_bank[c] for c in chunks],
                [x[:, c] for c in chunks], repeat(tol), repeat(max_iter),
            )

            iterations = 0
            for c, (r, t, it) in zip(chunks, results):
                R[A[c], B[c]] = r.T
                T[A[c], B[c]] = t.T
                iterations = max(iterations, it)

            if verbose and total % 20 == 0:
                print(f"A + B = {total:3}  (up to {iterations} iterations)", flush=True)

    return R, T, F


""" ---- Using the solution ---- """

def turn_policy(R, T, F, my_score, opp_score, first):
    """Values for every state of the current turn, as {(t, r1, r2, c): (stop, play)}.

    Each value is a tuple (P(I lose), -P(I win)), so smaller is better and the tuples
    compare in the same order the solver uses: least likely to lose, then most
    likely to win outright.

    first: True if this player is player 1 (moves first in each round)
    """
    max_bank = None
    if first:
        A, B = np.array([my_score]), np.array([opp_score])
        stop_loss, bust_loss, mover = p1_stop_loss(A, B, T, F), T[my_score, opp_score][:, None], 0
        max_bank = p1_max_bank(A, B)
    elif opp_score > TARGET:
        s = np.arange(NEED_CAP + 2)[:, None]
        stop_loss = final_turn_loss(np.array([[opp_score - my_score]]), s).transpose(0, 2, 1)
        bust_loss, mover = np.array([[0.0], [1.0]]), 1
    else:
        A, B = np.array([opp_score]), np.array([my_score])
        stop_loss, bust_loss, mover = p2_stop_loss(A, B, R), R[opp_score, my_score][:, None], 1

    record = {}
    solve_turn(stop_loss, bust_loss, mover, max_bank=max_bank, record=record)
    key = lambda v: (float(v[mover]), -float(v[1 - mover]))
    return {state: (key(stop), key(play)) for state, (stop, play) in record.items()}

def save(R, T, F, path='win_solution.pkl'):
    with open(path, 'wb') as f:
        pickle.dump(dict(R=R, T=T, F=F, target=TARGET), f)

def load(path='win_solution.pkl'):
    with open(path, 'rb') as f:
        d = pickle.load(f)
    return d['R'], d['T'], d['F']
