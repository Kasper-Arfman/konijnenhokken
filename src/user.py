from models import UI, GameState
from src.command_line import CommandUI
from src.bot_ui import BotUI

class User:

    def __init__(self, i, ui: UI=CommandUI):
        self.i = i
        self.ui = ui()

    def decide_allocation(self, gs: GameState):
        rabbits, cages = self.ui.on_decide_allocation(gs)
        return rabbits, cages

    def decide_continue(self, gs: GameState):
        choice = self.ui.on_decide_continue(gs)
        return choice
    
    def __repr__(self):
        return f"User({self.i})"








from collections import Counter


def encode_input(gs: GameState):

    score = [
        gs.run_score, 
        gs.turn_score, 
        gs.game_score
        ]
    

    r = Counter(gs.rabbits)
    c = Counter(gs.cages)
    b = Counter(gs.roll)
    r.get(1, None)


    r1 = [0] * 7; r1[r.get(1, 1)-1] = (1 if 1 in r else 0)
    r2 = [0] * 7; r2[r.get(2, 1)-1] = (1 if 2 in r else 0)
    c2 = [0] * 7; c2[r.get(2, 1)-1] = (1 if 2 in c else 0)
    c3 = [0] * 7; c3[r.get(3, 1)-1] = (1 if 3 in c else 0)
    c4 = [0] * 7; c4[r.get(4, 1)-1] = (1 if 4 in c else 0)
    c5 = [0] * 7; c5[r.get(5, 1)-1] = (1 if 5 in c else 0)
    b1 = [0] * 7; b1[b.get(1, 1)-1] = (1 if 1 in b else 0)
    b2 = [0] * 7; b2[b.get(2, 1)-1] = (1 if 2 in b else 0)
    b3 = [0] * 7; b3[b.get(3, 1)-1] = (1 if 3 in b else 0)
    b4 = [0] * 7; b4[b.get(4, 1)-1] = (1 if 4 in b else 0)
    b5 = [0] * 7; b5[b.get(5, 1)-1] = (1 if 5 in b else 0)
    b6 = [0] * 7; b6[b.get(6, 1)-1] = (1 if 6 in b else 0)

    rabbit = r1 + r2
    cages = c2 + c3  +c4 + c5
    board = b1 + b2  +b3  +b4  +b5  +b6

    print(f"{b1 = }")
    print(f"{b2 = }")
    print(f"{b3 = }")
    print(f"{b4 = }")
    print(f"{b5 = }")
    print(f"{b6 = }")
    return score + rabbit + cages + board

import numpy as np


def decode_output(nodes: list, gs: GameState):
    roll = Counter(gs.roll)

    # == Rabbits
    n1 = roll.get(1, 0)
    n2 = roll.get(2, 0)

    valid1 = nodes[8*0: 8*1][:n1]
    valid2 = nodes[8*1: 8*2][:n2]

    r1 = np.argmax(valid1) if valid1.size else 0
    r2 = np.argmax(valid2) if valid2.size else 0
    
    # - ensure atleast one rabbit
    if r1 == r2 == 0:
        if n1:  r1 = 1
        else:   r2 = 1

    rabbits = [1]*r1 + [2]*r2

    # == Cages
    #  - Apply mask
    c2 = nodes[7*2+0] if n2 > r2 else 0
    c3 = nodes[7*2+1] if 3 in roll else 0
    c4 = nodes[7*2+2] if 4 in roll else 0
    c5 = nodes[7*2+3] if 5 in roll else 0
    
    # - ensure subsequent numbers
    cages = []
    for i, x in enumerate([c2, c3, c4, c5], 2):
        if x < 0.5:  break
        cages.append(i)

    # == Roll again
    roll_again = True if nodes[-1] > 0.5 else False

    return rabbits, cages, roll_again




class BotUser(User):

    def __init__(self, i, ui: UI, strategy=None):
        self.i = i
        self.ui = ui() if ui else BotUI()
        self.strategy=strategy

    def decide_allocation(self, gs: GameState):
        # v_in = encode_input(gs)
        # v_out = self.strategy.activate(v_in)

        v_out = np.random.uniform(0, 1, 2*8+4+1)  # activate network
        rabbits, cages, _ = decode_output(v_out, gs)
        # print(f"{rabbits = }, {cages = }")
        return rabbits, cages

    def decide_continue(self, gs: GameState):
        v_out = np.random.uniform(0, 1, 2*8+4+1)  # activate network
        _, _, roll_again = decode_output(v_out, gs)
        # print(f"{roll_again = }")
        return roll_again
    
    def __repr__(self):
        return f"Bot({self.i})"
    
