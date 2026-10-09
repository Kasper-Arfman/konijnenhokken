from collections import Counter
from game.ui import UI
from game.state import UserState
from game.ui_cmd import CommandUI
from game.rules import allocations, points_stop, canonical

class User:

    def __init__(self, alias, ui: UI=None):
        self.alias = alias

        if ui is None:    
            from game.ui_graphical import GraphicalUI
            self.ui = GraphicalUI(self.alias)
        else:
            self.ui = ui

    def decide_allocation(self, gs: UserState):
        rabbits, cages = self.ui.on_decide_allocation(gs)
        return rabbits, cages

    def decide_continue(self, gs: UserState):
        choice = self.ui.on_decide_continue(gs)
        return choice
    
    def __repr__(self):
        return f"User({self.alias})"

class QBot(User):
    """Plays the single-player strategy: policy is the solution of solve_singleplayer.py"""

    def __init__(self, alias, policy: dict,  verbose=True):
        self.alias = alias
        self.policy = policy
        self.ui = CommandUI(alias) if verbose else UI(alias)

    @staticmethod
    def state_difference(a, b):
        """The dice that take state b to state a, like [1, 1, 2], [3, 4, 5]"""
        _, Ar1, Ar2, Ac = a
        _, Br1, Br2, Bc = b
        rabbits = [1]*(Ar1 - Br1) + [2]*(Ar2 - Br2)
        cages = [i+1 for i in range(Bc+1, Ac+1)]
        return rabbits, cages

    def decide_allocation(self, gs: UserState):
        """Pick the allocation with the highest expected score"""
        roll = Counter(gs.roll)
        state_value = lambda state: max(points_stop(state), self.play_value(state))
        best = max(allocations(gs.state, roll), key=state_value)
        return self.state_difference(best, gs.state)

    def decide_continue(self, gs: UserState):
        return self.play_value(gs.state) > gs.stop_score

    def play_value(self, state):
        return self.policy[canonical(state)]
