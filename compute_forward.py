"""
Given a value network, compute the expectation value
"""
from math import factorial, prod, comb
from collections import Counter
from itertools import combinations_with_replacement
from functools import cache

TURN_MAX = 1  # maximum turn_score to show
SCORE_MARGIN = 0   # only show moves that have a significant inpact
TERMINAL = 101  # Always stop if you reach this many points
NUM_DICE = 7
DICE_PROBABILITIES = {
    # 0: 4/6,  # no rabbit (3, 4, 5 or 6)
    1: 1/6,
    2: 1/6,
    3: 1/6,
    4: 1/6,
    5: 1/6,
    6: 1/6,
} 

LIBRARY = {}

# def survive(n: int):
#     """Probability to survive a dice roll of n dice"""
#     return 1 - DICE_PROBABILITIES[0]**n

def next_turn(state):
    if sum(state[1:]) != NUM_DICE:
        raise ValueError()

    t, r1, r2, c = state
    t += (r1 + 2*r2)*(c+1)
    return t, 0, 0, 0

def E(state):
    s = stop(state)
    p = play(state)
    result = max(s, p)

    LIBRARY[state] = (s, p)

    return result

def stop(state):
    """Value of cashing in points at this state"""
    t, r1, r2, c = state
    return t + (r1 + 2*r2)*(c+1)

@cache
def play(state):
    """ The expected value of a state
    To compute the expected score of a state:
     - Consider all possible dice rolls
     - For any dice roll, consider all possible allocations
    """
    # Base case: if the turn score is 100, we always stop
    if state[0] >= TERMINAL:
        result = 0
    
    # If no dice are left:
    elif sum(state[1:]) == NUM_DICE:
        result = E(next_turn(state))  ## * survive(NUM_DICE)  I think this is not needed. check later

    else:
        result = sum(P(r) * Q(state, r) for r in rolls(state) )

    # print(f"play{state} = {result:.2f}")
    return result

def rearrangements(roll: dict):
    """E.g. (1, 2, 2, 3) has twelve rearrangements"""
    f = factorial(sum(roll.values()))
    for v in roll.values():
        f //= factorial(v)
    return f

def P(roll: dict, p=DICE_PROBABILITIES):
    """The probability of a roll"""
    f = rearrangements(roll)
    return f * prod(p[dice]**count for dice, count in roll.items())

def Q(state, roll: dict):
    """ The expected value of a state, given a roll
    This is the expected value of the best choice
    """
    return max((E(ch) for ch in children(state, roll)), default=0)

def rolls(state):
    """Compute every possible roll as r1, r2, c
    
    This might be a bit hard with the cages: what about a roll like [1, 2, 2, 3]
    The naive approach is to just take a dict of 1 to 6, but this might be possible to simplify
    """
    dice_remaining = (NUM_DICE - sum(state[1:])) or NUM_DICE
    return [Counter(x) for x in combinations_with_replacement([1, 2, 3, 4, 5, 6], dice_remaining)]

def num_rolls(state, n=6):
    """How many unique rolls can be made with k n-sided dice"""
    k = NUM_DICE - sum(state[1:])
    return comb(n+k-1, k)

def children(state: tuple, roll: dict):
    # print(f'Childen of {state = }, {roll = }')

    """All the possible states that can be obtained from a roll"""
    t, r1, r2, c = state

    # if there are no dice left, you will start a new run
    if r1 + r2 + c == NUM_DICE:
        t += (r1 + 2*r2)*(c+1)
        r1, r2, c = 0, 0, 0
    
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
                # Add this possibility
                states.add((t, r1+d1, r2+d2, c+dc))

    # print(f"   => {states = }")
    return states



def main():
    max_score = E((0, 0, 0, 0))
    
    # Show all states where you should play
    for k in sorted(LIBRARY):
        s, p = LIBRARY[k]

        # if k[0] >= TURN_MAX:
        #     break
    
        if p > s + SCORE_MARGIN:
            print(f"{k} -- stop:{s:7.2f} play:{p:7.2f} {p-s:7.2f}")


    print(f"{max_score = }")
    import pickle
    with open('library.pkl', 'wb') as f:
        pickle.dump(LIBRARY, f)


if __name__ == "__main__":
    main()