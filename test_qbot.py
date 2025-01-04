import pickle
from src import Engine
from src.user import QBot, User
from src.bot_ui import BotUI
from src.command_line import CommandUI
from src.graphical import GraphicalUI

def load_Q(file_name):
    with open(file_name, 'rb') as f:
        return pickle.load(f)

# Q = r'C:\Users\arfma005\Documents\GitHub\konijnenhokken\.pkl\value_13.494.pkl'
NUMERICAL = load_Q(r'C:\Users\arfma005\Documents\GitHub\konijnenhokken\.pkl\library.pkl')

def main(n_turns=5):
    game = Engine([
        User(
            ui=GraphicalUI()
                ),
        QBot(
            ui=CommandUI(),
            policy=NUMERICAL,
                )
        ])
    game.play(n_turns)

    print(f"Game result:")
    for user in game.users:
        avg_score = game.gs[user].game_score / n_turns
        print(f" - {user}: {avg_score = :.3f}")

if __name__ == "__main__":
    main()
    

