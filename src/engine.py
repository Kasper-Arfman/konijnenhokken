from collections import Counter
from models import GameState
from src.user import User
from src.gamestate import UserGameState

class Engine:

    users: list[User]

    DEFAULT_NUM_DICE = 7
    RABBITS = {1, 2}
    CAGES = {2, 3, 4, 5}

    def __init__(self, users: list[User], *, n_dice=None):
        self.users = users
        self.n_dice = n_dice or self.DEFAULT_NUM_DICE
        self.gs = {user: UserGameState(self.n_dice) for user in self.users}

    """ ==== Core ==== """

    def play(self, rounds=1):
        """A game consists of r rounds
        In a round, every player takes one turn
        In one turn, a player may play any number of runs
        """
        for _ in range(rounds):
            for user in self.users:
                print(f"\nNow playing: {user}")
                self.take_turn(user)
        self.game_over()
        for user in self.users:
            gs = self.gs[user]
            user.ui.on_game_over(gs.read_only())

    def take_turn(self, user: User):
        gs = self.gs[user]
        gs.start_turn()
        user.ui.on_turn_start(gs.read_only())
        while True:
            gs.roll_dice()
            user.ui.on_dice_roll(gs.read_only())

            if self.turn_lost(gs):
                gs.lose_turn()
                user.ui.on_turn_lost(gs.read_only())
                break

            # ask the user how to allocate points
            rabbits, cages = self.request_allocation(gs, user)
            gs.allocate(rabbits, cages)
            user.ui.on_point_allocation(gs.read_only())

            if self.run_completed(gs):
                # Got rid of all the dice!
                gs.complete_run()
                user.ui.on_run_completed(gs.read_only())
            else:
                # Still in the same run
                # No need to update the game state here
                pass

            # ask the user if he wants to go again
            if not user.decide_continue(gs):
                gs.end_turn()
                user.ui.on_end_turn(gs.read_only())
                break

            user.ui.on_next_roll(gs.read_only())
        return
    
    """ ==== Interface with user ==== """

    def request_allocation(self, gs: GameState, user: User):
        rabbits, cages = user.decide_allocation(gs.read_only())
        status, message = self.validate_allocation(gs, rabbits, cages)
        while not status:
            user.ui.error_message(message)

            exit()  # remove this later!

            rabbits, cages = user.decide_allocation(gs.read_only())
            status, message = self.validate_allocation(gs, rabbits, cages)

        return rabbits, cages

    def validate_allocation(self, gs: GameState, rabbits: list, cages: list):
        roll = Counter(gs.roll)
        rabbits = Counter(rabbits)
        cages = Counter(cages)

        # - Chose atleast one rabbit
        if not rabbits:
            return False, f"Must take at least one rabbit"

        # - Chose a subset of the roll
        if not rabbits <= roll:
            return False, f"Don't spend rabbits you don't have"

        # - Contains only rabbits
        if not set(rabbits) <= self.RABBITS:
            return False, f"That's not a rabbit"
        
        # == Validate cages
        # - Chose a subset of the roll (after rabbits are removed)
        if not cages <= roll - rabbits:
            return False, f"Don't spend cages you don't have"

        # - Contains only cages
        if not set(cages) <= self.CAGES:
            return False, f'Not only cages'

        # - All cages occur once, and none have been selected before
        req = Counter(gs.cages) + cages
        if cages and any(req[x]!=1 for x in range(2, max(cages))):
            return False, f"Not unique, a gap, or missing the 2"

        return True, 'OK'

    """ ==== checking for events ==== """

    def turn_lost(self, gs: GameState):
        """The roll does not contain any rabbits"""
        return not set(gs.roll) & self.RABBITS

    def run_completed(self, gs: GameState):
        return not gs.dice_remaining

    def game_over(self, verbose=False):
        if verbose:
            print(f"\nGame Over")
            for user in self.users:
                gs = self.gs[user]
                print(f"user {user.i}: {gs.game_score} points")

