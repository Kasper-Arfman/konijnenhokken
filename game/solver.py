from math import factorial, prod
from collections import Counter
from itertools import combinations_with_replacement

cache = {}  # Store solutions here
DEPTH = 101  # Sufficiently large
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
    if state not in cache:
        # If no dice are left, start a new turn
        # Stores both (0, 7, 0, 0) and (7, 0, 0, 0), although they are identical
        if sum(state[1:]) == NUM_DICE:
            cache[state] = play_value(next_turn(state))

        # Base case: stop if we have too many points
        elif state[0] >= DEPTH:
            cache[state] = -1
        
        else:
            cache[state] = sum(P(r) * E_roll(state, r) for r in rolls(state))
    
    return cache[state]

def E_roll(state, roll: dict):
    """Expected score - given a roll - of the best allocation"""
    return max((E(state) for state in possible_allocations(state, roll)), default=0)

def possible_allocations(state: tuple, roll: dict):
    """All the possible states that can be obtained from a roll"""
    t, r1, r2, c = state
    states = set()
    for d1 in range(roll[1]+1):
        for d2 in range(roll[2]+1):
            # Must add atleast one rabbit
            if (d1, d2) == (0, 0):  continue

            # 1: Add only rabbits
            states.add((t, r1+d1, r2+d2, c))

            # In case all 2s are used up
            if not (roll[2] - d2):  continue

            # 2: Add cages as well
            for dc, cage in enumerate(range(c+2, 6), 1):
                if cage not in roll:  break
                states.add((t, r1+d1, r2+d2, c+dc))
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

def sorted_dict(d: dict, value=False):
    """Sort a dict by key (default) or by value"""
    return dict(sorted(d.items(), key=lambda x:x[value]))