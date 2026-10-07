from math import factorial, prod
from collections import Counter
from itertools import combinations_with_replacement

cache = {}  # Store solutions here
DEPTH = 150  # Sufficiently large
NUM_DICE = 7
DICE_PROBABILITIES = {
    1: 1/6,  2: 1/6,
    3: 1/6,  4: 1/6,
    5: 1/6,  6: 1/6,
}

def solve():
    """Solves the game by finding the expected value for the first state.
    This is done by computing the expected play-value of all the children. Solutions are stored in the cache
    """
    global cache
    max_score = E((0, 0, 0, 0))  # Update cache
    Q = sorted_dict(cache)
    cache = {}  # clear cache
    return max_score, Q

def E(state):
    """Expectation value of a state"""
    return max(stop_value(state), play_value(state))

def stop_value(state):
    """Obtained score when stopping"""
    t, r1, r2, c = state
    return t + (r1 + 2*r2)*(c+1)


def play_value(state):
    """Expected score when rolling again"""
    state = canonical(state)
    if state not in cache:
        # Base case: stop if we have too many points
        if state[0] >= DEPTH:
            cache[state] = -1
        
        else:
            cache[state] = sum(P(r) * E_roll(state, r) for r in rolls(state))
    
    return cache[state]

def E_roll(state, roll: dict):
    """Expected score - given a roll - of the best allocation"""
    return max((E(state) for state in possible_allocations(state, roll)), default=0)

def possible_allocations(state: tuple, roll: dict):
    """All the possible states that can be obtained from a roll"""
    t, r1, r2, c = state  # turn score, ones as rabbit, twos as rabbit, cage multiplier
    states = set()
    for ones in range(roll[1]+1):  # ones spending
        for twos in range(roll[2]+1):  # twos spending
            # Must add atleast one rabbit
            if ones == twos == 0:  continue

            # Possibility 1: Add only rabbits
            states.add((t, r1+ones, r2+twos, c))

            # Possibility 2: Add cages as well
            for dc, cage in enumerate(range(c+2, 6), 1):
                # Cage die must be rolled; for x2, it must not be spent as rabbit
                if roll[cage] <= (twos if cage == 2 else 0):  break

                states.add((t, r1+ones, r2+twos, c+dc))
    return states

def P(roll: dict, p=DICE_PROBABILITIES):
    """The probability of a roll"""
    f = rearrangements(roll)
    return f * prod(p[dice]**count for dice, count in roll.items())

def rearrangements(roll: dict):
    """E.g. (1, 2, 2, 3) has twelve rearrangements"""
    f = factorial(sum(roll.values()))
    for v in roll.values():
        f //= factorial(v)
    return f

def rolls(state, options=[1, 2, 3, 4, 5, 6]):
    """Generate all possible dice rolls"""
    dice_remaining = NUM_DICE - sum(state[1:])
    return [Counter(x) for x in combinations_with_replacement(options, dice_remaining)]

def next_turn(state):
    """Transfer points"""
    return stop_value(state), 0, 0, 0

def canonical(state):
    """A full board is the same as banking the run and rolling 7 fresh dice,
    e.g. (100, 0, 4, 3) is the same state as (132, 0, 0, 0)"""
    return next_turn(state) if sum(state[1:]) == NUM_DICE else state

def sorted_dict(d: dict, value=False):
    """Sort a dict by key (default) or by value"""
    return dict(sorted(d.items(), key=lambda x:x[value]))