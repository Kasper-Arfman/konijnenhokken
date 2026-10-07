"""The same solution as solve_1v1.py, fast enough for TARGET = 200 (about 20 minutes).

States, formulas and the saved file are exactly those of solve_1v1.py; read that
first. Only the way of computing them is different:

1. Bottom-up instead of recursive.
   Game states are solved in order of decreasing A + B: every turn that doesn't
   bust leads to a larger A + B, which is then already solved. Inside a turn,
   t goes from high to low, and the dice used from 7 down to 0.

2. Many game states at once.
   Game states with the same A + B don't depend on each other, so their turns
   are solved together: each value is a numpy array with a column per game state.
   They are also split over the CPU cores.

3. Rolls are grouped.
   Rolls that allow the same allocations are merged into one, with their
   probabilities added up.

4. The bust loop is solved directly.
   With fixed decisions, a turn's value is linear in what busting is worth:
       Q = a + p_bust * bust_value
   so the loop between Q[(A, B, 0)] and Q[(A, B, 1)] has a direct solution. The
   decisions depend on the bust value, so this repeats until nothing changes.
"""
import os
import sys
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from game.rules import NUM_DICE, stop_score, rolls, possible_allocations
import solve_1v1
from solve_1v1 import P1, P2, P2_FINAL

VALUE, BUST = 0, 1  # Channels of a value array: win chance, and chance that the turn busts


""" ---- The turn as arrays (independent of the game state) ---- """

def build_turn_graph():
    """Number the boards (r1, r2, c), and group the rolls of each board by the allocations they allow"""
    boards = {(0, 0, 0)}
    todo = [(0, 0, 0)]
    groups = defaultdict(lambda: defaultdict(float))  # board => allocations => probability
    while todo:
        board = todo.pop()
        if sum(board) == NUM_DICE:  continue
        for p, roll in rolls((0,) + board):
            allocations = frozenset(T[1:] for T in possible_allocations((0,) + board, roll))
            groups[board][allocations] += p
            for new in allocations - boards:
                boards.add(new)
                todo.append(new)

    boards = sorted(boards)
    index = {board: i for i, board in enumerate(boards)}
    bust = len(boards)  # Extra row that holds the value of busting

    # One layer per number of dice used, from 6 down to 0. A layer only
    # depends on layers with more dice used, so they're solved in this order.
    layers = []
    for used in range(NUM_DICE - 1, -1, -1):
        layer = [board for board in boards if sum(board) == used]
        group_starts, probabilities, option_starts, options = [], [], [], []
        for board in layer:
            group_starts.append(len(probabilities))
            for allocations, p in groups[board].items():
                probabilities.append(p)
                option_starts.append(len(options))
                options.extend(sorted(index[b] for b in allocations) or [bust])
        layers.append(dict(
            boards=np.array([index[b] for b in layer]),
            group_starts=np.array(group_starts),
            probabilities=np.array(probabilities)[None, :, None],
            option_starts=np.array(option_starts),
            option_counts=np.diff(option_starts + [len(options)]),
            options=np.array(options),
        ))

    return dict(
        boards=boards,
        score=np.array([stop_score((0,) + board) for board in boards]),
        full=np.array([index[b] for b in boards if sum(b) == NUM_DICE]),
        empty=index[(0, 0, 0)],
        bust=bust,
        layers=layers,
    )

GRAPH = build_turn_graph()
MAX_RUN = int(GRAPH['score'].max())  # Highest score of a single run


""" ---- Solving many turns at once ---- """

def best(a, b):
    """Elementwise, the option with the higher win chance (a on a tie)"""
    return np.where(a[VALUE] >= b[VALUE], a, b)

def best_per_group(values, starts, counts):
    """The option with the highest win chance in each group of options"""
    result = np.empty((2, len(starts), values.shape[2]))
    result[VALUE] = np.maximum.reduceat(values[VALUE], starts, axis=0)
    chosen = values[VALUE] == np.repeat(result[VALUE], counts, axis=0)
    result[BUST] = np.minimum.reduceat(np.where(chosen, values[BUST], np.inf), starts, axis=0)
    return result

def solve_turns(stop_value, bust_value, max_bank):
    """Solve a batch of independent turns, one per column.

    stop_value: (S, batch) value of stopping with turn score s (beyond S - 1 counts as S - 1)
    bust_value: (batch,)   value of busting
    max_bank:   (batch,)   with more points banked, rolling 7 fresh dice isn't allowed

    Returns Q[S] and the chance that the turn busts, both (batch,)
    """
    g = GRAPH
    S, batch = stop_value.shape
    score, full = g['score'], g['full']

    # Sort the columns by max_bank, so the columns still in play are always the first k
    order = np.argsort(-max_bank, kind='stable')
    max_bank = max_bank[order]

    stop = np.zeros((2, S, batch))
    stop[VALUE] = stop_value[:, order]

    # fresh[t]: rolling 7 fresh dice with t points banked (-inf: not allowed)
    fresh = np.full((2, max_bank[0] + MAX_RUN + 1, batch), -np.inf)

    # values[board]: Q[S, (t, board)] for the current t
    values = np.zeros((2, len(g['boards']) + 1, batch))
    values[VALUE, g['bust']] = bust_value[order]
    values[BUST, g['bust']] = 1

    for t in range(max_bank[0], -1, -1):
        k = np.searchsorted(-max_bank, -t, side='right')  # Columns with max_bank >= t
        stop_t = stop[:, np.minimum(t + score, S - 1), :k]

        # Full board: stop, or bank the run and roll 7 fresh dice
        values[:, full, :k] = best(stop_t[:, full], fresh[:, t + score[full], :k])

        for layer in g['layers']:
            per_roll = best_per_group(values[:, layer['options'], :k], layer['option_starts'], layer['option_counts'])
            play = np.add.reduceat(per_roll * layer['probabilities'], layer['group_starts'], axis=1)
            boards = layer['boards']
            if boards[0] == g['empty']:
                fresh[:, t, :k] = play[:, 0]  # 7 fresh dice: you have to roll
            else:
                values[:, boards, :k] = best(stop_t[:, boards], play)

    result = np.empty((2, batch))
    result[:, order] = fresh[:, 0]
    return result[VALUE], result[BUST]


""" ---- Game states ---- """

def final_turns(n_max):
    """Q[(n, 0, 2)] for n = 0 .. n_max: P2's final turn, trailing by n"""
    n = np.arange(1, n_max + 1)
    s = np.arange(n_max + MAX_RUN + 1)[:, None]
    stop_value = np.where(s > n, 1.0, np.where(s == n, solve_1v1.TIE, 0.0))
    q, _ = solve_turns(stop_value, np.zeros(len(n)), max_bank=n)
    return np.concatenate([[np.nan], q])

def p1_turns(A, B, Q_p2, Q_final):
    """Stop values and max_bank for P1's turns at (A, B)"""
    target = solve_1v1.TARGET
    max_bank = np.maximum(target - 1 - A, B - A + solve_1v1.LEAD_CAP - 1)
    new_A = A + np.arange(max_bank.max() + MAX_RUN + 1)[:, None]
    gap = np.clip(new_A - B, 0, len(Q_final) - 1)
    stop_value = np.where(new_A >= target, 1 - Q_final[gap], 1 - Q_p2[np.minimum(new_A, target - 1), B])
    return stop_value, max_bank

def p2_turns(A, B, Q_p1):
    """Stop values and max_bank for P2's (regular) turns at (A, B)"""
    target = solve_1v1.TARGET
    max_bank = target - 1 - B
    new_B = B + np.arange(max_bank.max() + MAX_RUN + 1)[:, None]
    stop_value = np.where(new_B >= target, 1.0, 1 - Q_p1[A, np.minimum(new_B, target - 1)])
    return stop_value, max_bank

def solve_bust_loop(p1_stop, p1_bank, p2_stop, p2_bank, x, tol=1e-13, max_iter=50):
    """Q[(A, B, 0)] and Q[(A, B, 1)] for game states whose only unsolved dependency is the bust loop.

    x is a guess for Q[(A, B, 0)]. With fixed decisions:
        Q[(A, B, 0)] = x = a1 + p1 * (1 - y)      P1 busts: P2's turn at (A, B)
        Q[(A, B, 1)] = y = a2 + p2 * (1 - x)      P2 busts: P1's turn at (A, B)
    """
    for iteration in range(1, max_iter + 1):
        y, p2 = solve_turns(p2_stop, 1 - x, p2_bank)
        q1, p1 = solve_turns(p1_stop, 1 - y, p1_bank)
        a2 = y - p2 * (1 - x)
        a1 = q1 - p1 * (1 - y)
        x_new = (a1 + p1 * (1 - a2 - p2)) / (1 - p1 * p2)
        converged = np.abs(x_new - x).max() < tol
        x = x_new
        if converged:
            return x, a2 + p2 * (1 - x), iteration
    raise RuntimeError("The bust loop did not converge")

def solve(processes=None, verbose=True):
    """Q for every game state, as in solve_1v1.py"""
    target, processes = solve_1v1.TARGET, processes or os.cpu_count()

    # The largest gap P1 can leave behind for P2's final turn
    Q_final = final_turns(max(target, solve_1v1.LEAD_CAP) + MAX_RUN)
    Q_p1 = np.zeros((target, target))  # Q[(A, B, 0)]
    Q_p2 = np.zeros((target, target))  # Q[(A, B, 1)]

    with ProcessPoolExecutor(processes) as pool:
        for total in range(2 * (target - 1), -1, -1):
            A = np.arange(max(0, total - (target - 1)), min(total, target - 1) + 1)
            B = total - A

            # Guess for Q[(A, B, 0)]: a neighbour that is already solved
            if total == 2 * (target - 1):
                x = np.full(len(A), 0.5)
            else:
                x = np.where(A < target - 1, Q_p1[np.minimum(A + 1, target - 1), B], Q_p1[A, np.minimum(B + 1, target - 1)])

            # Split the game states over the CPU cores
            p1_stop, p1_bank = p1_turns(A, B, Q_p2, Q_final)
            p2_stop, p2_bank = p2_turns(A, B, Q_p1)
            chunks = [np.arange(i, len(A), processes) for i in range(min(processes, len(A)))]
            results = pool.map(
                solve_bust_loop,
                [p1_stop[:, c] for c in chunks], [p1_bank[c] for c in chunks],
                [p2_stop[:, c] for c in chunks], [p2_bank[c] for c in chunks],
                [x[c] for c in chunks],
            )
            iterations = 0
            for c, (q1, q2, it) in zip(chunks, results):
                Q_p1[A[c], B[c]] = q1
                Q_p2[A[c], B[c]] = q2
                iterations = max(iterations, it)

            if verbose and total % 20 == 0:
                print(f"A + B = {total:3}  ({iterations} iterations)", flush=True)

    Q = {}
    for A in range(target):
        for B in range(target):
            Q[A, B, P1] = float(Q_p1[A, B])
            Q[A, B, P2] = float(Q_p2[A, B])
    for n in range(1, len(Q_final)):
        Q[n, 0, P2_FINAL] = float(Q_final[n])
    return Q


def main():
    if len(sys.argv) > 1:
        solve_1v1.TARGET = int(sys.argv[1])
    Q = solve()
    solve_1v1.save(Q)
    p1_wins = Q[0, 0, P1]
    print(f"Target {solve_1v1.TARGET}: P1 win chance {p1_wins:.4%}, P2 win chance {1 - p1_wins:.4%}")
    print(f"Saved {len(Q)} game states to {solve_1v1.SOLUTION}")

if __name__ == "__main__":
    main()
