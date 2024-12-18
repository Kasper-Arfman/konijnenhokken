class GameState:

    rabbits: list
    cages: list

    total_dice: int
    game_score: int
    turn_score: int
    run_score: int
    rabbits: list
    cages: list
    roll: list
    dice_remaining: int

    def start_turn(self):
        raise NotImplementedError()

    def roll_dice(self):
        raise NotImplementedError()

    def lose_turn(self):
        raise NotImplementedError()

    def allocate(gs, rabbits: list, cages: list):
        raise NotImplementedError()

    def complete_run(self):
        raise NotImplementedError()

    def end_turn(self):
        raise NotImplementedError()

    def read_only(self):
        raise NotImplementedError()