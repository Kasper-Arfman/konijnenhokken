"""Find the strategy that maximizes win chance Q = p_win + 0.5*p_tie

Idea: pretend every value already exists in a lookup table. Then work out
(1) which entry depends on which, and (2) in what order to fill the tables.


== Notation

    S = (A, B, i)          # Game state at the START of a turn
                           #   A = points of player 1, B = points of player 2
                           #   i = player about to move (0 = P1, 1 = P2)
    T = (t, r1, r2, c)     # Turn state, after allocating a roll (as in solver.py)
                           #   t = points banked in earlier runs of this turn

    Q[S]     # Win chance of the player about to move, at the start of the turn
    Q[S, T]  # Win chance of the player moving, midway through the turn at T

    Every Q is from the point of view of the player MOVING in S.


== Why Q = p_win + 0.5*p_tie is convenient

    With this choice, my Q and my opponent's Q always add up to 1:
        Q_me + Q_opp = (p_win + p_tie/2) + (p_loss + p_tie/2) = 1
    So when the turn passes to the opponent:  value for me = 1 - Q[S_opponent]
    One number per state is enough.

    (If a tie counted as a full win for BOTH players, Q_me + Q_opp = 1 + p_tie.
     Then you would need to store two numbers per state, e.g. p_win and p_loss.)


== Leaves: the game is over

    The game ends after a round (P1's turn, then P2's turn) in which someone
    has reached 200 points (200 or more). Then, from P1's point of view:

        end_value_P1(A, B) = 1    if A > B
                           = 0.5  if A == B
                           = 0    if A < B

    The round is complete right after P2's turn. So the game can only end there.


== Ending a turn: where do you go next?

    Ending the turn with turn score s (s = 0 when you bust) brings you to:

    If P1 is moving (i = 0):
        S' = (A + s, B, 1)                  # P2's turn, always
        end_turn[S, s] = 1 - Q[S']

    If P2 is moving (i = 1):
        if max(A, B + s) >= 200:            # Round complete and 200 reached: game over
            end_turn[S, s] = 1 - end_value_P1(A, B + s)
        else:
            S' = (A, B + s, 0)              # Next round, P1's turn
            end_turn[S, s] = 1 - Q[S']

    This is the only place where the game state S changes.
    Everything inside a turn keeps S fixed and only changes T.


== Inside a turn (S is fixed)

    stop_score[T] = t + (r1 + 2*r2) * (c + 1)

    Player decision 1: allocating a roll
        T_roll[S, T, roll] = max(allocations[T|roll], key=lambda T': Q[S, T'])

        Value of the roll:
            roll_value[S, T, roll] = Q[S, T_roll[S, T, roll]]
            roll_value[S, T, roll] = end_turn[S, 0]          if allocations[T|roll] is empty (bust)

    Player decision 2: play or stop
        stop_value[S, T] = end_turn[S, stop_score[T]]
        play_value[S, T] = sum(P[roll] * roll_value[S, T, roll] for roll in rolls[T])

        Exception, all 7 dice used: playing means rolling 7 fresh dice
            play_value[S, T] = play_value[S, (stop_score[T], 0, 0, 0)]

        Q[S, T] = max(stop_value[S, T], play_value[S, T])

    Start of the turn: you must roll
        Q[S] = play_value[S, (0, 0, 0, 0)]

    Compare with solver.py: this is exactly the same recursion. The only change is
    that stop_value is end_turn[S, ...] instead of the score itself.


== Special case: P2's final turn

    If S = (A, B, 1) with A >= 200, the game ends after this turn whatever P2 does.
    B < 200 here (otherwise the game would have ended a round earlier), so the
    gap n = A - B is at least 1. end_turn only depends on n:
        end_turn = 1    if s > n
                 = 0.5  if s == n
                 = 0    if s < n     (including bust: s = 0)

    So Q[(A, B, 1)] = Q_final[A - B], one small table over n.
    This is NOT a fixed probability distribution: P2 plays to beat n.
    E.g. needing 3 points, P2 stops at 4, but needing 30, P2 keeps rolling.


== Dependencies

    Q[S]  ->  Q[S, T]  ->  Q[S, T'] (one roll later)  ->  ...  ->  end_turn[S, s]  ->  Q[S']

    Inside a turn:   every roll uses at least one die, or starts a fresh run with
                     higher t. So T only moves "forward" and there are no loops.
                     t grows without limit, though: cap it like DEPTH in solver.py
                     (stop when you are far above 200 anyway).

    Between turns:   S' = (A + s, B, ...) or (A, B + s, ...)
                     If s > 0, then A + B increases.
                     If you bust (s = 0), A + B stays the same:

                         (A, B, 0)  --P1 busts-->  (A, B, 1)  --P2 busts-->  (A, B, 0)

                     This is the only loop in the whole problem.


== Building the Q table

    Store Q[S]: about 200 x 200 x 2 entries, plus Q_final[n].
    Q[S, T] is only needed while solving the turn of S: other turns only use Q[S].
    You can keep it (to play without recomputing), but it is MUCH bigger:
        ~80,000 game states x ~10,000 turn states each = ~10^9 entries
        as a Python dict (~100 bytes per entry):  ~100 GB
        as a numpy float32 array:                 ~4 GB
    Recomputing Q[S, T] for one S when you need it takes a fraction of a second.

    1. Q_final[n] for every gap n
         One turn each, no dependencies on other game states.

    2. All other Q[S], in order of DECREASING A + B
         for total in range(398, -1, -1):
             for A + B == total:
                 every s > 0 leads to a larger A + B  ->  already in the table
                 only bust leads to the same A + B    ->  the loop above1 1

    3. Breaking the loop for one (A, B)
         The two unknowns are x = Q[(A, B, 0)] and y = Q[(A, B, 1)].
             x = turn_P1(bust value = 1 - y)
             y = turn_P2(bust value = 1 - x)
         Value iteration: guess y = 0.5, compute x, then y, then x, ...
         until they stop changing. A double bust happens rarely, so each step
         shrinks the error a lot and this converges quickly.

    4. Answer: Q[(0, 0, 0)] = P1's win chance; P2's is 1 - Q[(0, 0, 0)]


== Using it to play

    At the start of your turn in game state S:
        Compute Q[S, T] for every turn state T (one turn solve)
        Allocate:   pick T_roll[S, T, roll]
        Continue:   play if play_value[S, T] > stop_value[S, T]

"""
import sys
import threading
from game.solver import possible_allocations, rolls, P, stop_value as stop_score, NUM_DICE

TARGET = 200    # The game ends after the round in which someone reaches this
TIE = 0.5       # Value of a tie
LEAD_CAP = 150  # P1 stops rolling fresh dice when at TARGET or more and this far ahead
TOL = 1e-12     # Convergence of the bust loop

Q_start = {}  # Q[S]:    S => win chance of the player about to move
Q_mid = {}    # Q[S, T]: S => {T: win chance of the player moving}


""" ---- Game states ---- """

def Q(S):
    """Q[S]: win chance of the player about to move in game state S = (A, B, i)"""
    if S not in Q_start:
        A, B, i = S
        if i == 1 and A >= TARGET:
            Q_start[S] = solve_turn(S)  # P2's final turn: no loop
        else:
            solve_loop(A, B)
    return Q_start[S]

def solve_loop(A, B):
    """Q[(A, B, 0)] and Q[(A, B, 1)] depend on each other through busts.
    Value iteration: guess one, compute the other, and repeat until stable"""
    y = 0.5  # Guess for Q[(A, B, 1)]
    while True:
        Q_start[A, B, 1] = y                # P1's bust value comes from here
        Q_start[A, B, 0] = solve_turn((A, B, 0))
        y_new = solve_turn((A, B, 1))       # P2's bust value uses Q[(A, B, 0)]
        if abs(y_new - y) < TOL:  break
        y = y_new
    Q_start[A, B, 1] = y_new

def end_value_p1(A, B):
    """P1's value when the game is over"""
    return 1 if A > B else TIE if A == B else 0

def end_turn(S, s):
    """Value for the player moving in S of ending the turn with turn score s (bust: s = 0)"""
    A, B, i = S
    if i == 0:
        return 1 - Q((A + s, B, 1))
    if max(A, B + s) >= TARGET:
        return 1 - end_value_p1(A, B + s)
    return 1 - Q((A, B + s, 0))


""" ---- Turn states (S is fixed) ---- """

def solve_turn(S):
    """Q[S]: you must roll at the start of a turn"""
    Q_mid[S] = {}  # Start over: the bust value may have changed (see solve_loop)
    return play_value(S, (0, 0, 0, 0))

def Q_turn(S, T):
    """Q[S, T]: the better of stopping and playing on"""
    if sum(T[1:]) == NUM_DICE:
        T = (stop_score(T), 0, 0, 0)  # All dice used: bank the run, play on with 7 fresh dice

    table = Q_mid[S]
    if T not in table:
        stop = end_turn(S, stop_score(T))
        if stop == 1 or not may_play(S, T):  # Can't do better than a certain win
            table[T] = stop
        else:
            table[T] = max(stop, play_value(S, T))
    return table[T]

def play_value(S, T):
    """Average over all rolls of the value of the best allocation"""
    value = 0
    for roll in rolls(T):
        options = possible_allocations(T, roll)
        if options:
            value += P(roll) * max(Q_turn(S, T2) for T2 in options)
        else:
            value += P(roll) * end_turn(S, 0)  # Bust
    return value

def may_play(S, T):
    """Cap like DEPTH in solver.py: P1 doesn't roll fresh dice when far ahead past TARGET"""
    A, B, i = S
    if i == 1 or sum(T[1:]) > 0:  # Only limit rolling 7 fresh dice
        return True
    new_A = A + stop_score(T)
    return new_A < TARGET or new_A - B < LEAD_CAP


""" ---- Playing ---- """

def should_play(S, T):
    """Roll again if that is better than stopping (also when all dice are used)"""
    return Q_turn(S, T) > end_turn(S, stop_score(T))

def best_allocation(S, T, roll):
    return max(possible_allocations(T, roll), key=lambda T2: Q_turn(S, T2))


def main():
    print(f"P1 win chance: {Q((0, 0, 0)):.4%}")
    print(f"Game states: {len(Q_start)}, turn states: {sum(len(t) for t in Q_mid.values())}")

if __name__ == "__main__":
    # The recursion goes very deep: every turn can lead to another turn
    sys.setrecursionlimit(10**6)
    threading.stack_size(512 * 2**20)
    thread = threading.Thread(target=main)
    thread.start()
    thread.join()
