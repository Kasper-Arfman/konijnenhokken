from collections import Counter
from models import UI, GameState

class CommandUI(UI):

    def on_point_allocation(self, gs: GameState=None):
        print(f"{str(gs.rabbits):21} {str(gs.cages):21}")
        return

    def on_dice_roll(self, gs: GameState=None):
        """"""
        print(f" {str(gs.roll):21}", end=' ')

    def on_turn_start(self, gs: GameState=None):
        print(f" {'Roll':21} {'Rabbits':21} {'Cages':21}")

    def on_turn_lost(self, gs: GameState=None):
        print(f'=> Oh dear, no rabbits')
        print(f"{gs.turn_score} / {gs.game_score}")

    def on_run_completed(self, gs: GameState=None):
        # print(f" - Nice, you finished the dice!")
        return

    def on_next_roll(self, gs: GameState=None):
        # print(f" - Going to roll again...")
        return

    def on_end_turn(self, gs: GameState=None):
        #                   .
        print(f"{gs.turn_score} / {gs.game_score}")

    def on_decide_allocation(self, gs: GameState=None):
        rabbits = int_selection('Choose rabbits', (1, 2, 3))
        cages = int_selection('Choose cages', (2, 3, 4, 5))
        # print(f"{rabbits = } {cages = }")
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


