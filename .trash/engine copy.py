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






class Engine:
    MAX_DICE = 7
    MAX_MULTIPLIER = 5

    def __init__(self):
        self.dice = Counter()
        self.score = 0
        self.multiplier = 1
        self.tally = 0
        self.ui = UI()

    def play(self, rounds=1):
        for i in range(rounds):
            self.take_turn()

    def take_turn(self):
        while True:
            self.roll_dice(self.dice.total() or self.MAX_DICE)
            self.ui.show_roll(self.dice_str())

            # Game over: did not roll rabbits
            if not self.contains_rabbit(self.dice):
                self.lose_all_points()
                self.ui.game_over()
                break
            
            # choose a rabbit to add to the pen
            rabbits, cages = self.ui.allocate()

            # Validate selection
            pass

            # Add rabbits and cages
            self.rabbits += rabbits
            self.cages += cages
            self.ui.update_score(self.score)

            # Start a new run if no dice are left
            if self.dice.total() == 0:
                self.add_points_to_tally()
                self.ui.finished_run()
                continue

            if not self.ui.roll_again():
                break

        self.add_points_to_tally()
        self.ui.end_turn()
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


class UI:

    def allocate():
        ...

    def play():
        ...

    def show_roll(dice):
        print(f"\nRolled:\n{dice}")

    def game_over():
        print(f"\nOh dear, you died...")
        ...

    def update_score():
        print(f'\nNow at a total score: {self.tally} + {self.score}*{self.multiplier}')

    def finished_run():
        print('You finished your dice! Starting new run.')

    def roll_again():
        return user_selection_bool('Roll again?')
    
    def end_turn():
        print(f"Turn ended with {self.tally} points!")

def main():
    game = Engine()
    game.play()

if __name__ == "__main__":
    main()