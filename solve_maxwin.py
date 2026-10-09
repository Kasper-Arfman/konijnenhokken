import sys
import threading
from game.rules import TURN_START, canonical, dice_left, points_stop, rolls, allocations


TARGET = 20    # The game ends after the round in which someone reaches this
TOL = 1e-12    # Convergence of the bust loop

P1, P2, P2_FINAL = 0, 1, 2

_Q = {}       # Cache of turn starts:   S => win chance of the player to move
_Q_turn = {}  # Cache of turn states:   S => {T: Q_play(S, T)}, only while solving the turn of S


def Q(S, T=TURN_START):
    """Win chance of the player to move in game state S = (A, B, i), turn state T"""
    if T == TURN_START:
        return Q_start(S)
    return max(Q_stop(S, T), Q_play(S, T))

def Q_stop(S, T):
    return end_turn(S, points_stop(T))

def end_turn(S, n):
    """Win chance of ending the turn with n points (bust: n = 0)"""
    A, B, i = S
    if i == P1:
        if A + n >= TARGET:  return 1 - Q((A + n, B, P2_FINAL))  # P2 gets one last turn
        return 1 - Q((A + n, B, P2))
    if i == P2:
        if B + n >= TARGET:  return 1                           # P2 finishes the round ahead
        return 1 - Q((A, B + n, P1))
    # P2_FINAL: the game is over
    return 1 if B + n > A else 0.5 if B + n == A else 0

def Q_play(S, T):
    T = canonical(T)  # e.g. (0, 0, 6, 1) becomes (24, 0, 0, 0)
    table = _Q_turn[S]
    if T not in table:
        if not worth_rolling(S, T):  table[T] = 0  # Base case: stopping is better
        else:                        table[T] = sum(p * Q_roll(S, T, roll) for p, roll in rolls(T))
    return table[T]

def Q_roll(S, T, roll):
    return max((Q(S, T2) for T2 in allocations(T, roll)), default=Q_bust(S))

def Q_bust(S):
    return end_turn(S, 0)

def worth_rolling(S, T):
    """Even if every roll that doesn't bust won the game, rolling must beat stopping"""
    p_bust = (4/6) ** dice_left(T)
    return Q_stop(S, T) < p_bust * Q_bust(S) + (1 - p_bust)


""" ---- Turn starts, and the bust loop ---- """

def Q_start(S):
    A, B, i = S
    if i == P2_FINAL:
        S = (A - B, 0, P2_FINAL)  # Only the gap matters
    if S not in _Q:
        if i == P2_FINAL:  _Q[S] = solve_turn(S)  # Busting ends the game: no loop
        else:              solve_loop(A, B)       # Busting hands the same scores back and forth
    return _Q[S]

def solve_turn(S):
    """At the start of a turn you must roll"""
    _Q_turn[S] = {}
    value = Q_play(S, TURN_START)
    del _Q_turn[S]
    return value

def solve_loop(A, B):
    """(A, B, P1) busts to (A, B, P2), which busts back to (A, B, P1).
    Guess Q((A, B, P2)), solve both turns, and repeat until the guess stops changing"""
    p1, p2 = (A, B, P1), (A, B, P2)
    _Q[p2] = 0.5
    while True:
        _Q[p1] = solve_turn(p1)  # A bust reads the guess _Q[p2] instead of recursing
        new = solve_turn(p2)     # A bust reads _Q[p1]
        converged = abs(new - _Q[p2]) < TOL
        _Q[p2] = new
        if converged:  break


def main():
    global TARGET
    if len(sys.argv) > 1:
        TARGET = int(sys.argv[1])
    q = Q((0, 0, P1))  # Player 1 begins
    print(f"TARGET {TARGET}: P1 win chance {q:.4%}, P2 win chance {1 - q:.4%} ({len(_Q)} game states)")

if __name__ == "__main__":
    # Every turn can lead to another turn, so the recursion goes very deep
    sys.setrecursionlimit(10**6)
    threading.stack_size(255 * 2**20)
    thread = threading.Thread(target=main)
    thread.start()
    thread.join()
