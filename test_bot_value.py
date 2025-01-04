import pickle
import neat
import os
from src import Engine
from src.user import ValueBot
from src.bot_ui import BotUI
from src.command_line import CommandUI

VALUE_FILE = r'C:\Users\arfma005\Documents\GitHub\konijnenhokken\value_13.494.pkl'

def load_values(value_file):
    with open(value_file, 'rb') as f:
        values = pickle.load(f)
    return values


def main(n_turns=1_000):

    ui = BotUI()
    # ui = CommandUI()

    bot = ValueBot(ui=ui,
        net=load_values(VALUE_FILE))

    game = Engine([
        bot,
            ])
    game.play(n_turns)

    print(f"Game result:")
    for user in game.users:
        avg_score = game.gs[user].game_score / n_turns
        print(f" - {user}: {avg_score = :.3f}")

if __name__ == "__main__":
    main()