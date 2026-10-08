from math import factorial, prod
from collections import Counter
from itertools import combinations_with_replacement
import pickle

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
        else:              _Q[T] = sum(P(roll) * Q_roll(T, roll) for roll in rolls(T))
    return _Q[T]

def Q_roll(T, roll: dict):
    return max((Q(T2) for T2 in allocations(T, roll)), default=0)

def allocations(T: tuple, roll: dict):
    t, r1, r2, c = T
    states = set()
    for ones in range(roll[1]+1):
        for twos in range(roll[2]+1):
            if ones == twos == 0:  continue  # Must add atleast one rabbit

            states.add((t, r1+ones, r2+twos, c))  # Adding only rabbits is one possibility

            # Alternatively, add any number of cages as well
            for dc, cage in enumerate(range(c+2, 6), 1):
                if roll[cage] <= (twos if cage == 2 else 0):  break  # Played my only two for points

                states.add((t, r1+ones, r2+twos, c+dc))
    return states

def P(roll: dict):
    f = probability_weight(roll)
    return f * prod((1/6)**count for count in roll.values())

def probability_weight(roll: dict):
    """E.g. (1, 2, 2, 3) has twelve rearrangements"""
    f = factorial(sum(roll.values()))
    for v in roll.values():
        f //= factorial(v)
    return f

def rolls(T, options=(1, 2, 3, 4, 5, 6)):
    dice_remaining = NUM_DICE - sum(T[1:])
    return [Counter(x) for x in combinations_with_replacement(options, dice_remaining)]


if __name__ == "__main__":
    Q((0, 0, 0, 0))  # This call builds the cache (_Q)

    _Q = {T: Q_T for T, Q_T in sorted(_Q.items()) if Q_T > points_stop(T)}  # Only include play-states

    FILENAME = __file__.rstrip('.py') + '.pkl'
    with open(FILENAME, 'wb') as f:
        pickle.dump(_Q, f)