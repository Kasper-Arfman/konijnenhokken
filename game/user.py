from collections import Counter
from game.ui import UI
from game.state import UserState
from game.ui_cmd import CommandUI
from game.solver import possible_allocations, stop_value, canonical

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

    def __init__(self, alias, policy: dict,  verbose=True):
        self.alias = alias
        self.policy = policy
        self.ui = CommandUI(alias) if verbose else UI(alias)

    @staticmethod
    def state_difference(a, b):
        """Format  the state difference like
        
        [1, 1, 2], [3, 4, 5]
        """

        _, Ar1, Ar2, Ac = a
        _, Br1, Br2, Bc = b
        dr1 = Ar1 - Br1
        dr2 = Ar2 - Br2
        dc  = Ac  - Bc

        rabbits = [1]*dr1 + [2]*dr2
        cages = [i+1 for i in range(Bc+1, Ac+1)]
        # print(f" state diff: {rabbits = } {cages = }")

        return rabbits, cages



        return dr1, dr2, dc
    
    def decide_allocation(self, gs: UserState):
        """Find all the states that can be reached from here
        Pick the one with the largest score."""
        roll = Counter(gs.roll)
        state_value = lambda state: max(stop_value(state), self.play_value(state))
        best = max(possible_allocations(gs.state, roll), key=state_value)
        return self.state_difference(best, gs.state)

    def decide_continue(self, gs: UserState):
        stop = gs.stop_score
        play = self.play_value(gs.state)
        return play > stop
    
    def play_value(self, state):
        return self.policy[canonical(state)]