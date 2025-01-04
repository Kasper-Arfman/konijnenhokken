import pickle
import numpy as np
import neat
import os
import random
from collections import Counter
from functools import cache
import neat.threaded
import pickle



def iter_states():
    for turn_score in range(100):
        for r1 in range(8):
            for r2 in range(8-r1):
                for c in range(min(8-r1-r2, 5)):
                    yield (turn_score, r1, r2, c)

def init_states():
    return {state: id for id, state in enumerate(iter_states())}

# == Load the state value data
VALUE_FILE = r'C:\Users\arfma005\Documents\GitHub\konijnenhokken\value_13.494.pkl'
with open(VALUE_FILE, 'rb') as f:
    values = pickle.load(f)
    values = np.array(values)

# Map states to their value
state_value = {state: value for state, value in zip(iter_states(), values)}


# Bot logic:

def possible_states(r1, r2, c, roll: tuple):
    roll = Counter(roll)
    states = set()
    for d1 in range(roll[1]+1):
        for d2 in range(roll[2]+1):
            # Must add atleast one rabbit
            if (d1, d2) == (0, 0):  continue

            # 1: Add only rabbits
            states.add((r1+d1, r2+d2, c))

            # In case all 2s are used up
            if not (roll[2] - d2):  continue

            # 2: Add cages as well
            for dc, cage in enumerate(range(c+2, 6), 1):
                if cage not in roll:  break
                # Add this possibility
                states.add((r1+d1, r2+d2, c+dc))

    return states

def state_difference(a, b):
    _, Ar1, Ar2, Ac = a
    _, Br1, Br2, Bc = b
    dr1 = Ar1 - Br1
    dr2 = Ar2 - Br2
    dc  = Ac  - Bc
    return dr1, dr2, dc

def decide_allocation(state, roll: tuple, state_value: dict):
    """Find all the states that can be reached from here
    Pick the one with the largest score."""
    # Find all the possible destination states
    # - the turn score remains unchanged
    t, r1, r2, c = state
    dest = [(t, *s) for s in possible_states(r1, r2, c, tuple(roll))]

    # Find the destination state that has the max value
    best = max(dest, key=state_value.get)
    return state_difference(best, state)

def decide_continue(state, state_value: dict):
    turn_score, r1, r2, c = state
    stop = turn_score + (r1 + 2*r2) * (c+1)
    play = state_value[state]
    return play > stop

