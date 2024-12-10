from collections import Counter

class UI:

    def update_allocation(self, *args):
        ...

    def update_dice(self, roll: Counter):
        print(f'You rolled: {sorted(roll.elements())}')

    def update_round_score(self, *args):
        ...

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


