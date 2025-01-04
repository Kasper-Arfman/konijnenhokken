from copy import deepcopy
import random
from models import GameState

class UserGameState(GameState):

    rabbits: list
    cages: list

    def __init__(self, n_dice: int):
        self.total_dice = n_dice
        self.game_score = 0
        self.turn_score = 0
        self.run_score = 0
        self.rabbits = []
        self.cages = []
        self.roll = []
        self.dice_remaining = self.total_dice

    """  ==== User Events ==== """

    @property
    def state(self):
        t = self.turn_score
        r1 = self.rabbits.count(1)
        r2 = self.rabbits.count(2)
        c = len(self.cages)
        return (t, r1, r2, c)
    
    @property
    def stop_score(self):
        t, r1, r2, c = self.state
        return t + (r1 + 2*r2) * (c+1)


    def start_turn(self):
        # Get all dice back
        self.dice_remaining = self.total_dice
        self.turn_score = 0

    def roll_dice(self):
        # Update gs.roll
        self.roll = sorted([
            random.randint(1, 6) \
                for _ in range(self.dice_remaining)])

    def lose_turn(self):
        # Lose run and turn points
        self.run_score = 0
        self.turn_score = 0

        # Lose all rabbits and cages
        self.rabbits = []
        self.cages = []

        # Lose all dice
        self.dice_remaining = 0
        self.roll = []

    def allocate(gs, rabbits, cages):
        # Turn dice into rabbits
        for val in rabbits:
            gs.roll.remove(val)
        gs.rabbits.extend(rabbits)

        # Turn dice into cages
        for val in cages:
            gs.roll.remove(val)
        gs.cages.extend(cages)

        # Update run score
        gs.run_score = (1+len(gs.cages)) * sum(gs.rabbits)

        # Update remaining dice
        gs.dice_remaining -= len(rabbits) + len(cages)

    def complete_run(self):
        # Transfer run_score to turn score
        self.turn_score += self.run_score
        self.run_score = 0

        # Lose all rabbits and cages
        self.rabbits = []
        self.cages = []

        # Regain all dice
        self.dice_remaining = self.total_dice

    def end_turn(self):
        # Transfer run_score to turn score
        self.turn_score += self.run_score
        self.run_score = 0

        # Increase game score by turn score, lose turn points
        self.game_score += self.turn_score
        # self.turn_score = 0

        # Lose all rabbits and cages
        self.rabbits = []
        self.cages = []

        # Lose all dice
        self.dice_remaining = 0
        self.roll = []

    def read_only(self):
        copy = deepcopy(self)
        # print(f"{copy = }")
        return copy

    def __repr__(self):
        return f"{self.rabbits = }\n{self.cages = }\n{self.turn_score = }\n{self.game_score = }\n{self.dice_remaining = }"
