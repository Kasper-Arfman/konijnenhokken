from models import GameState

class UI:

    def on_point_allocation(self, gs: GameState=None):
        raise NotImplementedError()

    def on_dice_roll(self, gs: GameState=None):
        raise NotImplementedError()

    def on_turn_start(self, gs: GameState=None):
        raise NotImplementedError()

    def on_turn_lost(self, gs: GameState=None):
        raise NotImplementedError()

    def on_run_completed(self, gs: GameState=None):
        raise NotImplementedError()

    def on_next_roll(self, gs: GameState=None):
        raise NotImplementedError()

    def on_end_turn(self, gs: GameState=None):
        raise NotImplementedError()

    def on_decide_allocation(self, gs: GameState=None):
        raise NotImplementedError()

    def on_decide_continue(self, gs: GameState=None):
        raise NotImplementedError()
    
    def on_game_over(self, gs: GameState=None):
        raise NotImplementedError()
    
    def error_message(self, message):
        raise NotImplementedError()

