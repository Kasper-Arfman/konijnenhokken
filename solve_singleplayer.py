"""Find the strategy that maximizes the expected score of a turn.

Every turn state T = (t, r1, r2, c) has a value: the expected score of the rest
of the turn when you play optimally.

    E[T]    = max(stop_score(T), play[T])                                 stop, or roll again
    play[T] = sum(p * max(E[T'] for T' in allocations(T, roll))           roll, then allocate
              for p, roll in rolls(T))                                    (busting scores 0)

E calls play, and play calls E for the states one roll later. The recursion ends
because every roll puts at least one die on the board. A full board starts a new
run with more points banked, so above DEPTH banked points we simply stop.

The play values are memoized in `play_values`, and saved to SOLUTION.
See SOLVER.md for a longer explanation.
"""
import pickle
import sys
from game.rules import TURN_START, points_stop, canonical, rolls, allocations

DEPTH = 201  # Always stop with this many points banked (rolling on stops paying off above 100)
SOLUTION = 'solution_singleplayer.pkl'

play_values = {}  # T => expected score when rolling again


def E(state):
    """Expected score of a state: the better of stopping and rolling again"""
    return max(points_stop(state), play_value(state))

def play_value(state):
    """Expected score when rolling again"""
    state = canonical(state)
    if state not in play_values:
        if state[0] >= DEPTH:
            play_values[state] = -1  # Never roll again
        else:
            play_values[state] = sum(p * roll_value(state, roll) for p, roll in rolls(state))
    return play_values[state]

def roll_value(state, roll):
    """Expected score after a roll: the value of the best allocation, 0 if you bust"""
    return max((E(s) for s in allocations(state, roll)), default=0)


""" ---- Using the solution ---- """

def best_allocation(Q, state, roll):
    """The allocation with the highest expected score"""
    value = lambda s: max(points_stop(s), Q[canonical(s)])
    return max(allocations(state, roll), key=value)

def should_play(Q, state):
    """Roll again if that has a higher expected score than stopping"""
    return Q[canonical(state)] > points_stop(state)

def load(path=SOLUTION):
    with open(path, 'rb') as f:
        return pickle.load(f)


def main():
    sys.setrecursionlimit(10_000)  # The recursion is a few runs of up to 7 rolls deep
    expected = play_value(TURN_START)
    Q = dict(sorted(play_values.items()))

    with open(SOLUTION, 'wb') as f:
        pickle.dump(Q, f)
    print(f"Expected score per turn: {expected:.4f}")
    print(f"Saved {len(Q)} play values to {SOLUTION}")

if __name__ == "__main__":
    main()
