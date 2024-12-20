from src import Engine, User, GraphicalUI, BotUser, CommandUI, BotUI
import pickle

import neat

import random
# random.seed(10)

def main(n_turns=1000):
    
    # == Construct a bot == #
    with open('best.pkl', 'rb') as f:
        best = pickle.load(f)

    config = neat.Config(neat.DefaultGenome, 
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        r'C:\Users\arfma005\Documents\GitHub\konijnenhokken\config-feedforward.txt')
    net = neat.nn.FeedForwardNetwork.create(best, config)
    bot = BotUser(2, BotUI, net=net)

    # == Set up the game
    # player = User(3, GraphicalUI)
    users = [
        bot,
        # player,
        ]
    game = Engine(users)

    # == Play the game
    game.play(n_turns)

    # == Report the outcome
    print(f"Game result:")
    for user in game.users:
        avg_score = game.gs[user].game_score / n_turns
        print(f" - {user}: {avg_score = :.3f}")

if __name__ == "__main__":
    main()