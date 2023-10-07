from collections import Counter
import random

def user_selection(prompt, options: tuple = None):
    options = tuple(options)
    assert options, 'Valids must not be empty'
    if all(type(x) == int for x in options):
        return int(user_selection(prompt, map(str, options)))
    choice = input(f"{prompt} {options}: ")
    while choice not in options:
        choice = input(f'... Try again {options}: ')
    return choice

def user_selection_bool(prompt):
    return user_selection(prompt, options=('y', 'n')) == 'y'

class RabbitCages:
    MAX_DICE = 7
    MAX_MULTIPLIER = 5

    def __init__(self):
        self.dice = Counter()
        self.score = 0
        self.multiplier = 1
        self.tally = 0

    def play(self, rounds=1):
        for i in range(rounds):
            self.take_turn()

    def take_turn(self):
        while True:
            self.roll_dice(self.dice.total() or self.MAX_DICE)
            print(f"\nRolled:\n{self.dice_str()}")
            if not self.contains_rabbit(self.dice):
                print(f"\nOh dear, you died...")
                self.lose_all_points()
                break
            
            # choose a rabbit to add to the pen
            while True:
                choice = user_selection('Select rabbit to add to the pen', 
                    options=set(self.dice) & {1, 2})
                self.dice[choice] -= 1
                self.score += choice
                if self.dice[choice] == 0:
                    del self.dice[choice]
                if not self.contains_rabbit(self.dice):  break
                if not user_selection_bool('Add more rabbits?'):  break

            # choose multipliers to add to the pen
            while True:
                if not self.multiplier_available(): break
                if not user_selection_bool('Add multiplier?'):  break
                self.multiplier += 1
                self.dice[self.multiplier] -= 1
                if self.dice[self.multiplier] == 0:
                    del self.dice[self.multiplier]
            
            print(f'\nNow at a total score: {self.tally} + {self.score}*{self.multiplier}')

            # Start a new run if no dice are left
            if self.dice.total() == 0:
                self.add_points_to_tally()
                print('You finished your dice! Starting new run.')
                continue

            if not user_selection_bool('Roll again?'):
                break

        self.add_points_to_tally()
        print(f"Turn ended with {self.tally} points!")
        self.lose_all_points()

    def roll_dice(self, n):
        self.dice = Counter(sorted(random.randint(1, 6) for _ in range(n)))
    
    def contains_rabbit(self, dice: dict):
        return dice.get(1) or dice.get(2)
    
    def multiplier_available(self):
        if not self.multiplier < self.MAX_MULTIPLIER:  return False
        return self.multiplier + 1 in self.dice

    def dice_str(self):
        return '\n'.join(f"{k}: {v}" for k, v in self.dice.items())
    
    def add_points_to_tally(self):
        self.tally += self.score * self.multiplier
        self.score = 0
        self.multiplier = 1
        return self.tally

    def lose_all_points(self):
        self.tally = 0
        self.score = 0
        self.multiplier = 1

def main():
    game = RabbitCages()
    game.play()

if __name__ == "__main__":
    main()