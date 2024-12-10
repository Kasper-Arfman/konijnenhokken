import random
from collections import Counter
from models.user import User
random.seed(1)

class UserGameState:

    rabbits: Counter
    cages: Counter

    def __init__(self, n_dice: int):
        self.total_dice = n_dice
        self.init_round()

    def init_round(self):
        self.total_score = 0
        self.round_score = 0
        self.next_round()

    def next_round(self):
        self.rabbits = Counter()
        self.cages = Counter()
        self.total_score += self.round_score
        self.round_score = 0
        self.dice_remaining = self.total_dice

    def lose_round(self):
        self.round_score = 0
        self.next_round()

    def __repr__(self):
        return f"{self.rabbits = }\n{self.cages = }\n{self.round_score = }\n{self.total_score = }\n{self.dice_remaining = }"


class Engine:

    users: list[User]

    DEFAULT_NUM_DICE = 6

    def __init__(self, num_users, *, n_dice=None):
        self.users = [User(i) for i in range(num_users)]
        self.n_dice = n_dice or self.DEFAULT_NUM_DICE

        self.gs = {user: UserGameState(self.n_dice) for user in self.users}

    def play(self, rounds=1):
        for _ in range(rounds):
            for user in self.users:
                self.play_round(user)
        self.game_over()

    def play_round(self, user: User):
        gs = self.gs[user]
        print(f"\n\nStarting a new round with {user}")

        while True:
            roll = self.roll_dice(gs.dice_remaining)
            user.ui.update_dice(roll)

            if self.round_lost(roll):
                gs.lose_round()
                user.ui.update_round_score(gs.round_score)
                print(f'Oh dear, no rabbits')
                break

            # ask the user how to allocate points
            allocation = self.get_point_allocation(gs, roll, user)

            # allocate points
            self.allocate_points(gs, allocation)
            user.ui.update_allocation()
            user.ui.update_round_score()
            print(gs.round_score, gs.total_score)

            if self.round_won(gs):
                gs.next_round()

            # ask the user if he wants to go again
            if not user.decide_continue():
                gs.next_round()
                break

        # end the round
        print(f"Round ended with {gs.total_score} points")

    def set_round_score(self, gs: UserGameState, score):
        gs.round_score = score

    def round_lost(self, roll):
        return (1 not in roll) and (2 not in roll)
    
    def round_won(self, gs: UserGameState):
        return not gs.dice_remaining

    def roll_dice(self, n):
        return Counter(random.randint(1, 6) for _ in range(n))
    
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
        gs.round_score = mul * rab
        return

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


