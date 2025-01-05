from collections import Counter
from game.ui import UI
from game.state import UserState

class CommandUI(UI):

    def on_decide_allocation(self, gs: UserState=None):
        rabbits = int_selection('Choose rabbits', (1, 2, 3))
        cages = int_selection('Choose cages', (2, 3, 4, 5))
        return rabbits, cages

    def on_decide_continue(self, gs: UserState=None):
        return user_selection_bool('Continue?')
    

    def on_turn_start(self, gs: UserState):
        print(f"\nNow playing: {self.alias}")
        print(f" {'Roll':21} {'Rabbits':21} {'Cages':21}")

    def on_dice_roll(self, gs: UserState):
        print(f" {str(gs.roll):21}", end=' ')

    def on_point_allocation(self, gs: UserState=None):
        print(f"{str(gs.rabbits):21} {str(gs.cages):21}")

    def on_turn_lost(self, gs: UserState=None):
        print(f'=> Oh dear, no rabbits')
        print(f"{gs.turn_score} / {gs.game_score}")

    # def on_run_completed(self, gs: GameState=None): ...

    # def on_next_roll(self, gs: GameState=None): ...

    def on_end_turn(self, gs: UserState=None):
        print(f"{gs.turn_score} / {gs.game_score}")

    # def on_game_over(self, gs: GameState=None): ...
    
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

def user_selection_bool(prompt):
    return user_selection(prompt, options=('y', 'n')) == 'y'

def user_selection(prompt, options: tuple = None):
    options = tuple(options)
    assert options, 'Valids must not be empty'
    if all(type(x) == int for x in options):
        return int(user_selection(prompt, map(str, options)))
    choice = input(f"{prompt} {options}: ")
    while choice not in options:
        choice = input(f'... Try again {options}: ')
    return choice




