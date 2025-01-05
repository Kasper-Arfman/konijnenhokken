from game.state import UserState

class UI:

    def __init__(self, alias):
        self.alias = alias

    def on_point_allocation(self, gs: UserState=None):
        return

    def on_dice_roll(self, gs: UserState=None):
        return

    def on_turn_start(self, gs: UserState=None):
        return

    def on_turn_lost(self, gs: UserState=None):
        return

    def on_run_completed(self, gs: UserState=None):
        return

    def on_next_roll(self, gs: UserState=None):
        return

    def on_end_turn(self, gs: UserState=None):
        return
    
    def on_game_over(self, gs: UserState=None):
        return
    
    def error_message(self, message):
        print(f"ERROR: {message}")