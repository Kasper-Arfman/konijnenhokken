from math import factorial
from collections import Counter
from functools import cache
from itertools import combinations_with_replacement
import pickle

# Using policy iteration, obtain Q quickly

_Q = dict()  # Cache


DEPTH = 133
NUM_DICE = 7

def Q(T):
    """Quality of state T"""
    return max(Q_stop(T), Q_play(T))

def Q_stop(T):
    return points_stop(T)

def points_stop(T):
    t, r1, r2, c = T
    return t + (r1 + 2*r2)*(c+1)

def Q_play(T):
    # If the state has all dice allocated, treat it as the state that follows
    # e.g. (0, 0, 6, 1) becomes (24, 0, 0, 0)
    if sum(T[1:]) == NUM_DICE:
        T = (points_stop(T), 0, 0, 0)
    
    if T not in _Q:
        if T[0] >= DEPTH:  _Q[T] = -1  # Base case: stop if we have too many points
        else:              _Q[T] = sum(p * Q_roll(T, roll) for p, roll in rolls(T))
    return _Q[T]

def Q_roll(T, roll: tuple):
    return max((Q(T2) for T2 in allocations(T, roll)), default=0)

def allocations(T: tuple, roll: tuple):
    t, r1, r2, c = T
    return [(t, *board) for board in _allocations((r1, r2, c), roll)]

@cache
def _allocations(board: tuple, roll: tuple):
    """The boards (r1, r2, c) you can move to. Doesn't depend on t, so it's cached per board"""
    r1, r2, c = board
    boards = set()
    for ones in range(roll[1]+1):
        for twos in range(roll[2]+1):
            if ones == twos == 0:  continue  # Must add atleast one rabbit

            boards.add((r1+ones, r2+twos, c))  # Adding only rabbits is one possibility

            # Alternatively, add any number of cages as well
            for dc, cage in enumerate(range(c+2, 6), 1):
                if roll[cage] <= (twos if cage == 2 else 0):  break  # Played my only two for points

                boards.add((r1+ones, r2+twos, c+dc))
    return tuple(boards)  # A tuple: the cached result is shared, so it mustn't be changed

def P(roll: tuple):
    f = probability_weight(roll)
    return f * (1/6)**sum(roll)

def probability_weight(roll: tuple):
    """E.g. (1, 2, 2, 3) has twelve rearrangements"""
    f = factorial(sum(roll))
    for v in roll:
        f //= factorial(v)
    return f

def rolls(T):
    return _rolls(NUM_DICE - sum(T[1:]))

@cache
def _rolls(dice_remaining, options=(1, 2, 3, 4, 5, 6)):
    """[(probability, roll), ...]. A roll counts each face: roll[face], with roll[0] unused,
    e.g. (1, 2, 2, 3) is (0, 1, 2, 1, 0, 0, 0). A tuple, so it can be a cache key"""
    result = []
    for x in combinations_with_replacement(options, dice_remaining):
        counts = Counter(x)
        roll = tuple(counts[face] for face in range(7))
        result.append((P(roll), roll))
    return result


if __name__ == "__main__":
    Q((0, 0, 0, 0))  # This call builds the cache (_Q)

    _Q = {T: Q_T for T, Q_T in sorted(_Q.items()) if Q_T > points_stop(T)}  # Only include play-states

    FILENAME = __file__.removesuffix('.py') + '.pkl'
    with open(FILENAME, 'wb') as f:
        pickle.dump(_Q, f)