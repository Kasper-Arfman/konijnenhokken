from models.ui import UI

class User:

    def __init__(self, i, ui: UI=None):
        self.i = i
        self.ui = ui or UI()
        self.total_score = 0
        self.round_score = 0

    def choose_point_allocation(self):
        allocation = self.ui.choose_point_allocation()
        return allocation

    def decide_continue(self):
        choice = self.ui.decide_continue()
        return choice
    
    def __repr__(self):
        return f"User({self.i})"
