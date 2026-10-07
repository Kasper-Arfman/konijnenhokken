"""The rules of Konijnenhokken that the solvers need: rolls, allocations and scores.

A turn state is a tuple T = (t, r1, r2, c):
    t   points banked in earlier runs of this turn (a run ends when all dice are used)
    r1  dice kept as 1-rabbits (1 point each)
    r2  dice kept as 2-rabbits (2 points each)
    c   cages collected, in order x2, x3, x4, x5. Only the highest counts: the multiplier is c + 1

Cages use up dice too, so r1 + r2 + c dice are on the board.
"""
from collections import Counter
from functools import cache
from itertools import combinations_with_replacement
from math import factorial

NUM_DICE = 7
FACES = (1, 2, 3, 4, 5, 6)
TURN_START = (0, 0, 0, 0)


def stop_score(state):
    """Points you bank by stopping now"""
    t, r1, r2, c = state
    return t + (r1 + 2*r2) * (c + 1)

def dice_left(state):
    """Number of dice you roll next"""
    return NUM_DICE - sum(state[1:])

def canonical(state):
    """A full board is the same as banking the run and rolling 7 fresh dice:
    (100, 0, 4, 3) is the same state as (132, 0, 0, 0)"""
    if dice_left(state) == 0:
        return (stop_score(state), 0, 0, 0)
    return state


def rolls(state):
    """Every distinct roll of the dice you have left, with its probability: [(p, roll), ...]

    The order of the dice doesn't matter, so (1, 2, 2) and (2, 1, 2) are the same roll.
    Each roll is a Counter, e.g. {1: 1, 2: 2}.
    """
    return _rolls(dice_left(state))

@cache
def _rolls(num_dice):
    return [
        (probability(roll), roll)
        for roll in map(Counter, combinations_with_replacement(FACES, num_dice))
    ]

def probability(roll):
    """Probability of a roll: e.g. (1, 2, 2) can be rolled in 3 orders, each with probability (1/6)^3"""
    num_dice = roll.total()
    orders = factorial(num_dice)
    for count in roll.values():
        orders //= factorial(count)
    return orders / len(FACES)**num_dice


def possible_allocations(state, roll):
    """All the states you can move to after a roll. No states: you bust.

    - You must keep at least one rabbit (a 1 or a 2)
    - Cages are collected in order: the next cage needs the die c + 2
    - The x2 cage needs a 2 that you didn't keep as a rabbit
    """
    t, r1, r2, c = state
    states = set()
    for ones in range(roll[1] + 1):
        for twos in range(roll[2] + 1):
            if ones == twos == 0:  continue  # At least one rabbit

            # Only rabbits
            states.add((t, r1 + ones, r2 + twos, c))

            # Rabbits and cages, as many as the roll allows
            for new_cages, cage in enumerate(range(c + 2, 6), 1):
                if roll[cage] <= (twos if cage == 2 else 0):  break
                states.add((t, r1 + ones, r2 + twos, c + new_cages))
    return states
