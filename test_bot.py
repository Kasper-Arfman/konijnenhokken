import pickle
import neat
import os
from src import Engine, BotUser


local_dir = os.path.dirname(__file__)

CONFIG = neat.Config(neat.DefaultGenome, 
    neat.DefaultReproduction,
    neat.DefaultSpeciesSet,
    neat.DefaultStagnation,
    os.path.join(local_dir, 'config-feedforward.txt'))

def load_bot(file_name):
    with open(f'{file_name}.pkl', 'rb') as f:
        genome = pickle.load(f)
    net = neat.nn.FeedForwardNetwork.create(genome, CONFIG)
    return BotUser(net=net)

def main(n_turns=10_000):
    game = Engine([
        load_bot('genome_8d769'),
            ])
    game.play(n_turns)

    print(f"Game result:")
    for user in game.users:
        avg_score = game.gs[user].game_score / n_turns
        print(f" - {user}: {avg_score = :.3f}")

if __name__ == "__main__":
    main()