import random
from collections import Counter
from models import User, UserGameState


random.seed(1)



class Engine:

    users: list[User]

    DEFAULT_NUM_DICE = 6
    RABBITS = {1, 2}

    def __init__(self, num_users, *, n_dice=None):
        self.users = [User(i) for i in range(num_users)]
        self.n_dice = n_dice or self.DEFAULT_NUM_DICE

        self.gs = {user: UserGameState(self.n_dice) for user in self.users}

    def play(self, rounds=1):
        """A game consists of r rounds
        In a round, every player takes one turn
        In one turn, a player may play any number of runs
        """

        for _ in range(rounds):
            for user in self.users:
                self.take_turn(user)
        self.game_over()

    def take_turn(self, user: User):
        gs = self.gs[user]
        user.ui.on_turn_start(user)
        while True:
            roll = self.roll_dice(gs.dice_remaining)
            user.ui.on_dice_roll(roll)

            if self.turn_lost(roll):
                self.lose_turn(gs)
                user.ui.on_turn_lost(gs.turn_score)
                break

            # ask the user how to allocate points
            allocation = self.get_point_allocation(gs, roll, user)
            self.allocate_points(gs, allocation)
            user.ui.on_point_allocation(gs)

            if self.run_completed(gs):
                # Got rid of all the dice!
                self.complete_run(gs)
                user.ui.on_run_completed()
            else:
                # Still in the same run
                # No need to update the game state here
                pass

            # ask the user if he wants to go again
            if not user.decide_continue():
                self.end_turn()
                user.ui.on_end_turn()
                break

            user.ui.on_next_roll()
        return


    def roll_dice(self, n):
        return Counter(random.randint(1, 6) for _ in range(n))

    def turn_lost(self, roll):
        """The roll does not contain any rabbits"""
        return not set(roll) & self.RABBITS

    def lose_turn(self, gs: UserGameState):
        gs.turn_score = 0
        gs.next_run()

    def get_point_allocation(self, gs, roll, user: User):
        valid_selection = False
        while not valid_selection:
            allocation = user.choose_point_allocation()
            valid_selection = self.validate_allocation(gs, roll, allocation)
        return allocation

    def allocate_points(self, gs: UserGameState, allocation: tuple[Counter]):
        rabbits, cages = allocation
        gs.rabbits += rabbits
        gs.cages += cages

        gs.dice_remaining -= rabbits.total() + cages.total()

        mul = gs.cages.total() + 1
        rab = sum(k*v for k, v in rabbits.items())
        gs.turn_score = mul * rab
        return

    def run_completed(self, gs: UserGameState):
        return not gs.dice_remaining
    
    def complete_run(self, gs: UserGameState):
        gs.next_run()

    def end_turn(self, gs):
        ...

    def game_over(self):
        print(f"\nGame Over")

    def validate_allocation(self, gs: UserGameState, roll: Counter, allocation: tuple[Counter]):
        rabbits, cages = allocation

        # == Validate rabbits
        # - Chose atleats one rabbit
        if not rabbits:
            print(f"Must take at least one rabbit")
            return

        # - Chose a subset of the roll
        if not rabbits <= roll:
            print(r"Don't spend rabbits you don't have")
            return False

        # - Contains only rabbits
        if not set(rabbits) <= {1, 2}:
            print(f"That's not a rabbit")
            return False
        
        # == Validate cages
        # - Chose a subset of the roll (after rabbits are removed)
        if not cages <= roll - rabbits:
            print(f"Don't spend cages you don't have'")

        # - Contains only cages
        if not set(cages) <= {2, 3, 4, 5}:
            print('Not only cages')
            return False

        # - All cages occur once, and none have been selected before
        req = gs.cages + cages
        if cages and any(req[x]!=1 for x in range(2, max(cages))):
            print(f"Not unique, a gap, or missing the 2")
            return False

        return True


