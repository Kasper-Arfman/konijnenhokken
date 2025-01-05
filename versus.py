import pickle
from game import Engine, User, QBot

SOLUTION = 'solution.pkl'

def test_bot(n_turns=10):
    """Play a game against the bot"""
    game = Engine([
        # User('Human'),
        QBot('Bot', load_policy(SOLUTION), verbose=True)
        ])
    game.play(n_turns)

    print(f"Game result:")
    for user in game.users:
        avg_score = game.gs[user].game_score / n_turns
        print(f" - {user}: {avg_score = :.3f}")

def load_policy(file_name):
    with open(file_name, 'rb') as f:
        return pickle.load(f)

if __name__ == "__main__":
    test_bot()
    

