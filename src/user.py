import numpy as np
import random
from collections import Counter
from neat.nn import FeedForwardNetwork
from scipy.special import softmax
from models import UI, GameState
from src.command_line import CommandUI
from src.bot_ui import BotUI

def weighted_draw(arr, default=0):
    if not arr: return default

    arr = softmax(arr)
    i = random.choices(range(arr.size), weights=arr, k=1)[0]
    return i

def encode_input(gs: GameState, verbose=False):

    score = [
        gs.run_score, 
        gs.turn_score, 
        gs.game_score
        ]

    r = Counter(gs.rabbits)
    r1 = [0] * 7; r1[r.get(1, 1)-1] = (1 if 1 in r else 0)
    r2 = [0] * 7; r2[r.get(2, 1)-1] = (1 if 2 in r else 0)
    rabbit = r1 + r2

    c = Counter(gs.cages)
    c2 = [int(2 in c)]
    c3 = [int(3 in c)]
    c4 = [int(4 in c)]
    c5 = [int(5 in c)]
    cages = c2 + c3 + c4 + c5

    b = Counter(gs.roll)
    b1 = [0] * 7; b1[b.get(1, 1)-1] = (1 if 1 in b else 0)
    b2 = [0] * 7; b2[b.get(2, 1)-1] = (1 if 2 in b else 0)
    b3 = [0] * 7; b3[b.get(3, 1)-1] = (1 if 3 in b else 0)
    b4 = [0] * 7; b4[b.get(4, 1)-1] = (1 if 4 in b else 0)
    b5 = [0] * 7; b5[b.get(5, 1)-1] = (1 if 5 in b else 0)
    b6 = [0] * 7; b6[b.get(6, 1)-1] = (1 if 6 in b else 0)
    board = b1 + b2 + b3 + b4 + b5 + b6

    if verbose:
        print(f"\n== Net Input == ")
        print(f"{gs.rabbits = }:\n - {r1}\n - {r2}")
        print(f"{gs.cages = }:\n - {cages}")
        print(f"{gs.roll = }:\n 1: {b1}\n 2: {b2}\n 3: {b3}\n 4: {b4}\n 5: {b5}\n 6: {b6}")
    return score + rabbit + cages + board

def decode_output(nodes: list, gs: GameState, verbose=0):
    roll = Counter(gs.roll)

    # == Rabbits
    n1 = roll.get(1, 0)
    n2 = roll.get(2, 0)

    valid1 = nodes[0: 8][:n1]
    valid2 = nodes[8: 16][:n2]

    r1 = np.argmax(valid1) if valid1 else 0
    r2 = np.argmax(valid2) if valid2 else 0
    
    # - ensure atleast one rabbit
    if r1 == r2 == 0:
        if n1:  r1 = 1
        else:   r2 = 1

    rabbits = [1]*r1 + [2]*r2

    # == Cages
    c = Counter(gs.cages)
    #  - Ensure cages exist in roll
    # => otherwise, set this node to 0
    c2 = nodes[16] if n2 > r2 else 0
    c3 = nodes[17] if 3 in roll else 0
    c4 = nodes[18] if 4 in roll else 0
    c5 = nodes[19] if 5 in roll else 0

    # - Ensure don't have cages yet
    # => otherwise, don't consider this node
    m = max(c, default=1)
    options = [1, c2, c3, c4, c5][m:]

    # - ensure subsequent numbers
    cages = []
    for i, x in enumerate(options, m+1):
        if x < 0.5:  break
        cages.append(i)

    # == Roll again
    roll_again = bool(nodes[20] > 0.5)


    if verbose:
        print(f"\n==== Net Output ====")
        print(f"{[round(x, 1) for x in nodes]}")
        print("Rabbits1: {}".format([round(x, 1) for x in nodes[0: 8]]))
        print("Rabbits2: {}".format([round(x, 1) for x in nodes[8: 16]]))
        if verbose == 1:
            print(f" => {rabbits}")
            print(f"Cages: {[round(x, 1) for x in nodes[16: 20]]}")
            print(f" => {cages}")
        if verbose == 2:
            print(f"Roll Again?: {nodes[20]:.1f} => {roll_again}")

    return rabbits, cages, roll_again

def decode_output_mc(nodes: list, gs: GameState, verbose=0):
    roll = Counter(gs.roll)

    # == Rabbits
    n1 = roll.get(1, 0)
    n2 = roll.get(2, 0)
    r1 = weighted_draw(nodes[0: 0+n1])
    r2 = weighted_draw(nodes[8: 8+n2])
    # - ensure atleast one rabbit
    if r1 == r2 == 0:
        if n1:  r1 += 1
        else:   r2 += 1

    rabbits = [1]*r1 + [2]*r2
    roll[1] -= r1
    roll[2] -= r2

    # == Cages
    # - Check which cages are allowed
    c = Counter(gs.cages)
    pool = c + roll
    for i, amt in enumerate(range(2, 6)):
        if amt not in pool:
            break
    valids = nodes[16: 16+i]

    # - draw from valid cages
    i_cages = weighted_draw(valids)
    cages = [2, 3, 4, 5][:i_cages]
    cages = [x for x in cages if x not in c]  # excludes what you already own

    # == Roll again
    yes = nodes[20]
    roll_again = bool(weighted_draw([1-yes, yes]))

    if verbose:
        print(f"\n==== Net Output ====")
        print(f"{[round(x, 1) for x in nodes]}")
        print("Rabbits1: {}".format([round(x, 1) for x in nodes[0: 8]]))
        print("Rabbits2: {}".format([round(x, 1) for x in nodes[8: 16]]))
        if verbose == 1:
            print(f" => {rabbits}")
            print(f"Cages: {[round(x, 1) for x in nodes[16: 20]]}")
            print(f" => {cages}")
        if verbose == 2:
            print(f"Roll Again?: {nodes[20]:.1f} => {roll_again}")

    return rabbits, cages, roll_again


class User:

    def __init__(self, ui: UI=None):
        self.ui = ui or CommandUI()

    def decide_allocation(self, gs: GameState):
        rabbits, cages = self.ui.on_decide_allocation(gs)
        return rabbits, cages

    def decide_continue(self, gs: GameState):
        choice = self.ui.on_decide_continue(gs)
        return choice
    
    def __repr__(self):
        return f"User({self.i})"


class BotUser(User):

    def __init__(self, ui: UI=None, net: FeedForwardNetwork=None, verbose=False):
        self.ui = ui() if ui else BotUI()
        self.strategy = net
        self.verbose = verbose

    def decide_allocation(self, gs: GameState):
        v_in = encode_input(gs, verbose=self.verbose)
        v_out = self.strategy.activate(v_in)
        rabbits, cages, self.roll_again = decode_output_mc(v_out, gs, verbose=1 if self.verbose else 0)
        return rabbits, cages

    def decide_continue(self, gs: GameState):
        return self.roll_again
    
    def __repr__(self):
        return f"Bot({self.i})"
    
