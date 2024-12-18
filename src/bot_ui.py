from collections import Counter
from models import UI, GameState

class BotUI(UI):

    def on_point_allocation(self, gs: GameState=None):
        ...

    def on_dice_roll(self, gs: GameState=None):
        ...

    def on_turn_start(self, gs: GameState=None):
        ...

    def on_turn_lost(self, gs: GameState=None):
        ...

    def on_run_completed(self, gs: GameState=None):
        ...

    def on_next_roll(self, gs: GameState=None):
        ...

    def on_end_turn(self, gs: GameState=None):
        ...
    
    def on_game_over(self, gs: GameState=None):
        ...
    
    def error_message(self, message):
        print(f"ERROR: {message}")


