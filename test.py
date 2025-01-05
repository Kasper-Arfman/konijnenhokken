import pickle
from game import Engine, QBot

SOLUTION = 'solution.pkl'

def test_bot(n_turns=100_000):
    """Verify that the bot performs as expected"""
    game = Engine([
        QBot('Bot', policy=load_policy(SOLUTION), verbose=False)
        ])
    
    print(f"Playing {n_turns:_} turns...")
    game.play(n_turns)

    print(f"\nGame result:")
    for user in game.users:
        avg_score = game.gs[user].game_score / n_turns
        print(f" - {user}: {avg_score = :.3f}")

def load_policy(file_name):
    with open(file_name, 'rb') as f:
        return pickle.load(f)

if __name__ == "__main__":
    test_bot()