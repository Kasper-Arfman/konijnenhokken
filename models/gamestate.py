from collections import Counter

class UserGameState:

    rabbits: Counter
    cages: Counter

    def __init__(self, n_dice: int):
        self.total_dice = n_dice
        self.game_score = 0
        self.turn_score = 0
        self.run_score = 0
        self.clear()

    def next_run(self):
        """You finished all the dice and may start again"""
        self.turn_score += self.run_score
        self.run_score = 0
        self.clear()

    def lose_turn(self):
        """You didn't roll a rabbit and lose your points"""
        self.turn_score = 0
        self.run_score = 0
        self.clear()


    def end_turn(self):
        """You decided to stop and actually earned points."""
        self.game_score += self.turn_score + self.run_score
        self.run_score = 0
        self.turn_score = 0
        self.clear()

    def clear(self):
        self.rabbits = Counter()
        self.cages = Counter()
        self.dice_remaining = self.total_dice


    def __repr__(self):
        return f"{self.rabbits = }\n{self.cages = }\n{self.turn_score = }\n{self.game_score = }\n{self.dice_remaining = }"
