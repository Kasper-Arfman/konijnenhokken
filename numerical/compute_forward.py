from math import factorial, prod
from collections import Counter
from itertools import combinations_with_replacement
from functools import cache

DEPTH = 101  # Always stop if you reach this many points. Must be sufficiently large to find the solution
NUM_DICE = 7
DICE_PROBABILITIES = {
    1: 1/6,
    2: 1/6,
    3: 1/6,
    4: 1/6,
    5: 1/6,
    6: 1/6,
}

def E(state):
    s = stop_value(state)
    p = play_value(state)
    result = max(s, p)
    return result

def stop_value(state):
    """Value of cashing in points at this state"""
    t, r1, r2, c = state
    return t + (r1 + 2*r2)*(c+1)

Q = {}
def play_value(state):
    """ The expected value of a state
    To compute the expected score of a state:
     - Consider all possible dice rolls
     - For any dice roll, consider all possible allocations
    """
    if state not in Q:

        # If no dice are left, start a new turn
        if sum(state[1:]) == NUM_DICE:
            Q[state] = play_value(next_turn(state))

        # Base case: stop if we have too many points
        elif state[0] >= DEPTH:
            Q[state] = -1
        
        else:
            Q[state] = sum(P(r) * Emax(state, r) for r in rolls(state))
    
    return Q[state]

def Emax(state, roll: dict):
    """ The expected value of a state, given a roll
    This is the expected value of the best choice
    """
    return max((E(ch) for ch in children(state, roll)), default=0)

def children(state: tuple, roll: dict):
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
    t, r1, r2, c = state
    t += (r1 + 2*r2)*(c+1)
    return t, 0, 0, 0

def main():
    max_score = E((0, 0, 0, 0))
    print(f"{max_score = }")

    # Generate all states and compute the stop and start 
    global Q
    Q = dict(sorted(Q.items()))


    # for k, v in Q.items():
    #     if k[0] > 7:  break

    #     print(k, v)


    # Test a bot that applies this Q
    import pickle
    with open('library.pkl', 'wb') as f:
        pickle.dump(Q, f)

if __name__ == "__main__":
    main()