"""Find the 1v1 strategy that maximizes the chance of winning: Q = P(win) + TIE * P(tie)

== Rules

Players alternate turns. A round is P1's turn followed by P2's turn. The game ends
after the round in which someone reaches TARGET points; most points wins.

== States

    S = (A, B, i)        Game state at the start of a turn. A, B: points of P1, P2
                           i = 0: P1 to move
                           i = 1: P2 to move
                           i = 2: P2's final turn: P1 has reached TARGET. Only the gap
                                  n = A - B matters, so this state is S = (n, 0, 2)
    T = (t, r1, r2, c)   Turn state, as in solve_singleplayer.py

    Q[S]      win chance of the player about to move
    Q[S, T]   win chance of the player moving, midway through the turn

    Every Q is from the point of view of the player moving. With TIE = 0.5, my Q
    and my opponent's Q add up to 1, so when the turn passes to the opponent:
        my value = 1 - Q[opponent's state]

== Inside a turn: the same as solve_singleplayer.py, except for what stopping is worth

    Q[S, T]    = max(end_turn(S, stop_score(T)), play[S, T])
    play[S, T] = sum(p * max(Q[S, T'] for T' in allocations(T, roll))   (busting: end_turn(S, 0))
                 for p, roll in rolls(T))
    Q[S]       = play[S, TURN_START]                                    (you must roll)

== Ending a turn with turn score s (s = 0 when you bust)

    P1:           1 - Q[(A + s, B, 1)]
    P2:           1 if B + s >= TARGET (P2 wins), else 1 - Q[(A, B + s, 0)]
    P2's final:   1 if s > n, TIE if s == n, 0 if s < n

== The bust loop

    Every turn that doesn't bust increases A + B. Busting doesn't:
        Q[(A, B, 0)]  --P1 busts-->  Q[(A, B, 1)]  --P2 busts-->  Q[(A, B, 0)]
    Plain recursion would go around this loop forever, so solve_loop() solves
    the pair with value iteration: guess one, compute the other, repeat.

== Bounding the turn

    P2 stops as soon as stopping wins, so P2's turns can't go on forever.
    P1 doesn't roll 7 fresh dice when at TARGET or more and LEAD_CAP ahead.

This is pure Python and slow: use a small target, e.g. `python solve_1v1.py 20`.
For TARGET = 200, solve_1v1_fast.py computes the same tables with numpy.
"""
import pickle
import sys
import threading
from game.rules import TURN_START, NUM_DICE, stop_score, canonical, rolls, possible_allocations, dice_left

TARGET = 200    # The game ends after the round in which someone reaches this
TIE = 0.5       # Value of a tie
LEAD_CAP = 150  # P1 doesn't roll 7 fresh dice when at TARGET or more and this far ahead
TOL = 1e-12     # Convergence of the bust loop
SOLUTION = 'solution_1v1.pkl'

P1, P2, P2_FINAL = 0, 1, 2

Q_start = {}  # S => Q[S]
Q_mid = {}    # S => {T: Q[S, T]}, only while solving the turn of S


""" ---- Game states ---- """

def game_state(S):
    """P2's turn after P1 reached TARGET is a final turn, where only the gap matters"""
    A, B, i = S
    if i == P2 and A >= TARGET:
        return (A - B, 0, P2_FINAL)
    return S

def Q(S):
    """Q[S]: win chance of the player about to move in game state S"""
    S = game_state(S)
    A, B, i = S
    if S not in Q_start:
        if S[2] == P2_FINAL:
            Q_start[S] = solve_turn(S)  # No loop: the game ends after this turn
            del Q_mid[S]  # Only Q[S] is needed from now on
        else:
            solve_loop(A, B)
    return Q_start[S]

def solve_loop(A, B):
    """Q[(A, B, 0)] and Q[(A, B, 1)] depend on each other through busts.
    Value iteration: guess Q[(A, B, 1)], compute both turns, and repeat until stable"""
    p1, p2 = (A, B, P1), (A, B, P2)
    Q_start[p2] = 0.5  # Guess
    while True:
        Q_start[p1] = solve_turn(p1)  # When P1 busts, this uses Q_start[p2]
        new = solve_turn(p2)          # When P2 busts, this uses Q_start[p1]
        converged = abs(new - Q_start[p2]) < TOL
        Q_start[p2] = new
        if converged:  break
    del Q_mid[p1], Q_mid[p2]

def end_turn(S, s):
    """Value for the player moving in S of ending the turn with turn score s (bust: s = 0)"""
    A, B, i = S
    if i == P1:
        return 1 - Q((A + s, B, P2))
    if i == P2:
        if B + s >= TARGET:
            return 1  # The round is complete and P2 reached TARGET: P2 wins, since A < TARGET
        return 1 - Q((A, B + s, P1))
    n = A  # P2's final turn: the game is over
    return 1 if s > n else TIE if s == n else 0


""" ---- Turn states (S is fixed) ---- """

def solve_turn(S):
    """Q[S]: at the start of a turn you must roll"""
    Q_mid[S] = {}  # Start over: the bust value may have changed (see solve_loop)
    return play_value(S, TURN_START)

def Q_turn(S, T):
    """Q[S, T]: the better of stopping and rolling again"""
    T = canonical(T)
    table = Q_mid[S]
    if T not in table:
        stop = end_turn(S, stop_score(T))
        if stop == 1 or not may_play(S, T):  # Rolling can't beat a certain win
            table[T] = stop
        else:
            table[T] = max(stop, play_value(S, T))
    return table[T]

def play_value(S, T):
    """Win chance when rolling again: the best allocation of every roll"""
    value = 0
    for p, roll in rolls(T):
        options = possible_allocations(T, roll)
        if options:
            value += p * max(Q_turn(S, T2) for T2 in options)
        else:
            value += p * end_turn(S, 0)  # Bust
    return value

def may_play(S, T):
    """P1 doesn't roll 7 fresh dice when at TARGET or more and LEAD_CAP ahead"""
    A, B, i = S
    if i != P1 or dice_left(T) < NUM_DICE:
        return True
    new_A = A + stop_score(T)
    return new_A < TARGET or new_A - B < LEAD_CAP


""" ---- Using the solution ---- """

def turn_values(S):
    """Q[S, T] for every state of the turn in game state S (needs a solved Q_start)"""
    S = game_state(S)
    solve_turn(S)
    return Q_mid.pop(S)

def best_allocation(turn, T, roll):
    """The allocation with the highest win chance. turn: from turn_values(S)"""
    return max(possible_allocations(T, roll), key=lambda T2: turn[canonical(T2)])

def should_play(S, turn, T):
    """Roll again if that has a higher win chance than stopping"""
    return turn[canonical(T)] > end_turn(game_state(S), stop_score(T))

def save(Q, path=SOLUTION):
    with open(path, 'wb') as f:
        pickle.dump(dict(target=TARGET, tie=TIE, lead_cap=LEAD_CAP, Q=Q), f)

def load(path=SOLUTION):
    """Load a solution into Q_start, with the TARGET, TIE and LEAD_CAP it was solved for"""
    global TARGET, TIE, LEAD_CAP
    with open(path, 'rb') as f:
        solution = pickle.load(f)
    TARGET, TIE, LEAD_CAP = solution['target'], solution['tie'], solution['lead_cap']
    Q_start.clear()
    Q_start.update(solution['Q'])
    return Q_start


def main():
    global TARGET
    if len(sys.argv) > 1:
        TARGET = int(sys.argv[1])

    p1_wins = Q((0, 0, P1))
    save(dict(sorted(Q_start.items())))
    print(f"Target {TARGET}: P1 win chance {p1_wins:.4%}, P2 win chance {1 - p1_wins:.4%}")
    print(f"Saved {len(Q_start)} game states to {SOLUTION}")

if __name__ == "__main__":
    # Every turn can lead to another turn, so the recursion goes very deep
    sys.setrecursionlimit(10**6)
    threading.stack_size(255 * 2**20)  # The largest stack Windows allows
    thread = threading.Thread(target=main)
    thread.start()
    thread.join()
