import pickle
import sys
import threading
from game.rules import TURN_START, NUM_DICE, canonical, dice_left, points_stop, rolls, allocations

TARGET = 200    # The game ends after the round in which someone reaches this
TIE = 0.5       # Value of a tie
TOL = 1e-12     # Convergence of the bust loop
SOLUTION = 'solution_1v1.pkl'

P1, P2, P2_FINAL = 0, 1, 2

_Q = {}       # Cache of game states:  S => Q(S)
_Q_turn = {}  # Cache of turn states:  S => {T: Q_play(S, T)}, only while solving the turn of S


""" ---- Turn states: the same as solve_maxpoints, but valued in win chance ---- """

def Q_turn(S, T):
    """Quality of turn state T, in game state S"""
    return max(Q_stop(S, T), Q_play(S, T))

def Q_stop(S, T):
    return end_turn(S, points_stop(T))

def Q_play(S, T):
    T = canonical(T)
    n, _, i = S
    if i == P2_FINAL and 0 < T[0] < n and dice_left(T) == NUM_DICE:
        return Q((n - T[0], 0, P2_FINAL))  # Same as starting the final turn trailing by n - t

    table = _Q_turn[S]
    if T not in table:
        if not worth_rolling(S, T):  table[T] = 0  # Base case: stopping is better
        else:                        table[T] = sum(p * Q_roll(S, T, roll) for p, roll in rolls(T))
    return table[T]

def Q_roll(S, T, roll):
    return max((Q_turn(S, T2) for T2 in allocations(T, roll)), default=Q_bust(S))

def Q_bust(S):
    return end_turn(S, 0)

def worth_rolling(S, T):
    """Even if every roll that doesn't bust won the game, rolling must beat stopping"""
    p_bust = (4/6) ** dice_left(T)
    return Q_stop(S, T) < p_bust * Q_bust(S) + (1 - p_bust)


""" ---- Game states: S = (A, B, i), the scores and whose turn it is ---- """

def Q(S):
    """Win chance of the player about to start a turn in game state S"""
    S = game_state(S)
    if S not in _Q:
        if S[2] == P2_FINAL:  _Q[S] = solve_turn(S)  # The game ends after this turn
        else:                 solve_loop(*S[:2])     # P1 and P2 depend on each other through busts
    return _Q[S]

def solve_turn(S):
    """At the start of a turn you must roll"""
    _Q_turn[S] = {}  # Start over: the bust value may have changed (see solve_loop)
    value = Q_play(S, TURN_START)
    del _Q_turn[S]
    return value

def solve_loop(A, B):
    """Q((A, B, P1)) and Q((A, B, P2)) depend on each other through busts.
    Value iteration: guess Q((A, B, P2)), solve both turns, and repeat until stable"""
    p1, p2 = (A, B, P1), (A, B, P2)
    _Q[p2] = 0.5  # Guess
    while True:
        _Q[p1] = solve_turn(p1)  # When P1 busts, this uses _Q[p2]
        new = solve_turn(p2)     # When P2 busts, this uses _Q[p1]
        converged = abs(new - _Q[p2]) < TOL
        _Q[p2] = new
        if converged:  break

def game_state(S):
    """P2's turn after P1 reached TARGET is a final turn, where only the gap matters"""
    A, B, i = S
    if i == P2 and A >= TARGET:
        return (A - B, 0, P2_FINAL)
    return S

def end_turn(S, s):
    """Win chance for the player moving in S of ending the turn with s points (bust: s = 0)"""
    A, B, i = S
    if i == P1:
        return 1 - Q((A + s, B, P2))
    if i == P2:
        if B + s >= TARGET:  return 1  # P2 completes the round on TARGET, while A < TARGET
        return 1 - Q((A, B + s, P1))
    n = A  # P2's final turn: the game is over
    return 1 if s > n else TIE if s == n else 0


""" ---- Using the solution ---- """

def turn_values(S):
    """Q_turn(S, T) for every turn state T reached in game state S (needs a solved _Q)"""
    S = game_state(S)
    _Q_turn[S] = {}
    Q_play(S, TURN_START)
    table = _Q_turn.pop(S)
    return {T: max(Q_stop(S, T), q) for T, q in table.items()}

def best_allocation(turn, T, roll):
    """The allocation with the highest win chance. turn: from turn_values(S)"""
    return max(allocations(T, roll), key=lambda T2: turn[canonical(T2)])

def should_play(S, turn, T):
    """Roll again if that has a higher win chance than stopping"""
    return turn[canonical(T)] > end_turn(game_state(S), points_stop(T))

def save(Q, Q_final, path=SOLUTION):
    """Q: (A, B, i) => Q(S) for A, B < TARGET and i in (P1, P2).
    Q_final: n => Q((n, 0, P2_FINAL)), for every n where Q(S) > 0 (the rest count as 0)"""
    with open(path, 'wb') as f:
        pickle.dump(dict(target=TARGET, Q=Q, Qfinal=Q_final), f)

def load(path=SOLUTION):
    """Load a solution into _Q, with the TARGET it was solved for"""
    global TARGET
    with open(path, 'rb') as f:
        solution = pickle.load(f)
    TARGET = solution['target']
    _Q.clear()
    _Q.update(solution['Q'])
    _Q.update({(n, 0, P2_FINAL): q for n, q in solution['Qfinal'].items()})
    return _Q

def report(path=SOLUTION):
    """Sanity checks of a saved solution"""
    with open(path, 'rb') as f:
        solution = pickle.load(f)
    Q, Q_final = solution['Q'], solution['Qfinal']
    p1_wins = Q[0, 0, P1]
    print(f"Saved to {path}: keys {sorted(solution)}, target {solution['target']}")
    print(f"Q: {len(Q)} entries (target * target * 2 = {solution['target'] ** 2 * 2})")
    print(f"Qfinal: {len(Q_final)} entries, gaps {min(Q_final)} .. {max(Q_final)}, "
          f"Qfinal[{max(Q_final)}] = {Q_final[max(Q_final)]:.3g}")
    print(f"Q[(0, 0, 0)] = {p1_wins:.6f}: P1 win chance {p1_wins:.4%}, P2 win chance {1 - p1_wins:.4%}")


def main():
    global TARGET
    if len(sys.argv) > 1:
        TARGET = int(sys.argv[1])

    Q((0, 0, P1))  # This call builds the cache (_Q)
    Q_game = {S: q for S, q in sorted(_Q.items()) if S[2] != P2_FINAL}
    Q_final = {S[0]: q for S, q in sorted(_Q.items()) if S[2] == P2_FINAL and q > 0}
    save(Q_game, Q_final)
    report()

if __name__ == "__main__":
    # Every turn can lead to another turn, so the recursion goes very deep
    sys.setrecursionlimit(10**6)
    threading.stack_size(255 * 2**20)  # The largest stack Windows allows
    thread = threading.Thread(target=main)
    thread.start()
    thread.join()
