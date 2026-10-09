from functools import cache
from solve_maxpoints import points_stop, allocations
from solve_final import SolverFinalTurn, _rolls

TARGET   = 10
NUM_DICE = 7
T0       = (0, 0, 0, 0)  # initial state of a turn
ROLLS    = {n: _rolls(n) for n in range(1, NUM_DICE+1)}  # ROLLS[dice] -> [(p, roll)]

_Q        = {}  # Q[S][T] -> float
_Q_T0     = {}  # Solutions where T=T0
_Q_T0_EST = {}  # contains guesses to be refined

def Q_T0(S):
    """Win probability for the player to move at the start of their turn in S"""
    a, b, i = S
    if game_over(S):    return 1 if a > b else 0.5 if a == b else 0
    if final_turn(S):   return Q_final(S[0] - S[1])  # B must beat A's score in one turn
    if S in _Q_T0:      return _Q_T0[S]
    if S in _Q_T0_EST:  return _Q_T0_EST[S]  # Solving in progress

    solve_Q_T0(S)  # resolve infinite loop (S -> bust -> bust -> S) using value iteration
    for S_ in (S, bust(S)):
        if S_ in _Q_T0_EST:  _Q_T0[S_] = _Q_T0_EST.pop(S_)  # Converged on a solution
    return _Q_T0[S]

def solve_Q_T0(S, tolerance=1e-6):
    """Compute initial states using value iteration"""
    S_bust = bust(S)
    _Q_T0_EST[S] = 0.5  # guess once
    while True:
        old = _Q_T0_EST[S]

        # Refine the guess by completing one cycle: S = bust(bust(S))
        _Q_T0_EST[S_bust] = solve_turn(S_bust)
        _Q_T0_EST[S]      = solve_turn(S)

        if abs(_Q_T0_EST[S] - old) < tolerance:
            break

    return _Q_T0_EST[S]

def solve_turn(S):
    """Value of the turn of S, with a fresh table: the bust value may have changed since last time"""
    _Q[S] = {}
    value = Q(S, T0)
    del _Q[S]  # If we don't need to remember all mid-turn solutions
    return value

def Q(S, T):
    q_stop = Q_stop(S, T)
    if q_stop == 1:  return q_stop      # Stopping already wins for sure
    return max(q_stop, Q_play(S, T))

def Q_stop(S, T):
    return 1 - Q_T0(stop(S, T)) # I win = 1 - you win

def Q_play(S, T):
    # All dice placed: bank them on the board and roll all dice again
    if sum(T[1:]) == NUM_DICE:
        T = (points_stop(T), 0, 0, 0)

    table = _Q[S]
    if T not in table:
        if not worth_rolling(S, T):  table[T] = Q_stop(S, T)  # Base case: stopping is better
        else:                        table[T] = sum(p * Q_roll(S, T, roll) for p, roll in ROLLS[NUM_DICE - sum(T[1:])])
    return table[T]

def worth_rolling(S, T):
    """Even if every roll that doesn't bust won the game, rolling must beat stopping"""
    p_bust = (4/6) ** (NUM_DICE - sum(T[1:]))
    return Q_stop(S, T) < p_bust * (1 - Q_T0(bust(S))) + (1 - p_bust)

def Q_roll(S, T, roll):
    options = allocations(T, roll)
    if not options:
        return 1 - Q_T0(bust(S))
    return max(Q(S, T_next) for T_next in options)

def bust(S):
    return (*S[:2], 1-S[2])

def stop(S, T):
    """Player i banks the points of T, then it's the other player's turn"""
    a, b, i = S
    if i == 0:  return (a + points_stop(T), b, 1)    # A banks, B to move
    else:       return (a, b + points_stop(T), 0)    # B banks, A to move

def final_turn(S):
    """B's turn after A reached the target: the game ends after this turn"""
    a, b, i = S
    return i == 1 and a >= TARGET

@cache
def Q_final(gap):
    """Win probability of B's final turn, trailing by `gap` points (solve_final)"""
    return SolverFinalTurn(gap).Q_play(T0)

def game_over(S):
    """The round ends after B's turn: when A is to move again and someone reached the target"""
    a, b, i = S
    return i == 0 and max(a, b) >= TARGET