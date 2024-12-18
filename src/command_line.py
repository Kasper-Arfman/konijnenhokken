from collections import Counter
from models import UI, GameState

class CommandUI(UI):

    def on_point_allocation(self, gs: GameState=None):
        print(gs.run_score, gs.turn_score, gs.game_score)

    def on_dice_roll(self, gs: GameState=None):
        roll = gs.roll
        print(f' - Bot rolled: {roll}')

    def on_turn_start(self, gs: GameState=None):
        print(f"\n\nBot starting a new round.")

    def on_turn_lost(self, gs: GameState=None):
        print(f' => Oh dear, no rabbits')

    def on_run_completed(self, gs: GameState=None):
        print(f" - Nice, you finished the dice!")

    def on_next_roll(self, gs: GameState=None):
        print(f" - Going to roll again...")

    def on_end_turn(self, gs: GameState=None):
        print(f" => Ending the turn now")
        print(f"{gs.game_score}")

    def on_decide_allocation(self, gs: GameState=None):
        rabbits = int_selection('Choose rabbits', (1, 2, 3))
        cages = int_selection('Choose cages', (2, 3, 4, 5))
        return rabbits, cages

    def on_decide_continue(self, gs: GameState=None):
        return user_selection_bool('Continue?')
    
    def on_game_over(self, gs: GameState=None):
        return
    
    def error_message(self, message):
        print(f"ERROR: {message}")



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


