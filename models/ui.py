from collections import Counter
from models import UserGameState

class UI:

    def on_point_allocation(self, gs: UserGameState):
        print(gs.run_score, gs.turn_score, gs.game_score)

    def on_dice_roll(self, roll: Counter):
        print(f'You rolled: {sorted(roll.elements())}')

    def on_turn_start(self, user):
        print(f"\n\nStarting a new round with {user}")

    # def on_run_start(self):
    #     ...

    def on_turn_lost(self, *args):
        print(f'Oh dear, no rabbits')

    def on_run_completed(self, *args):
        print(f"Nice, you finished the dice!")

    def on_next_roll(self):
        print(f"Going to roll again...")

    def on_end_turn(self):
        print(f"Ending the turn now")

    def choose_point_allocation(self, *args):
        rabbits = int_selection('Choose rabbits', (1, 2, 3))
        cages = int_selection('Choose cages', (2, 3, 4, 5))
        return rabbits, cages

    def decide_continue(self, *args):
        return user_selection_bool('Continue?')

def int_selection(prompt: str, options: set=None):
    choices = input(f"{prompt} {options}: ").split()
    try:
        choices = Counter([int(c) for c in choices])
    except ValueError:
        return int_selection('Thats not ints', options)
    
    if options and not all(c in options for c in choices):
        return int_selection('Thats not an option', options)

    return choices


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


