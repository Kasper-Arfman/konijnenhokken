import concurrent.futures
from neat.nn import FeedForwardNetwork
import neat
from neat.config import Config
from neat.genome import DefaultGenome
from typing import List, Tuple


# Pygame shutup
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'True'

from src import Engine, BotUser, BotUI, CommandUI

NUM_TURNS = 250

Genomes = List[Tuple[int, DefaultGenome]]

def evaluate_genome(genome_id: int, genome: DefaultGenome, config: Config):
    genome.fitness = 0

    # Play the game with each genome
    net = FeedForwardNetwork.create(genome, config)
    user = BotUser(genome_id, net=net, ui=None, verbose=False)
    game = Engine([user])
    game.play(NUM_TURNS)

    # Calculate fitness
    genome.fitness = game.gs[user].game_score / NUM_TURNS
    return genome_id, genome

def f(arg):
    genome_tuple, config = arg
    return evaluate_genome(*genome_tuple, config)

def eval_genomes(genomes: Genomes, config):
    args = ((genome, config) for genome in genomes)
    # f = lambda genome_tuple: evaluate_genome(*genome_tuple, config)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results: Genomes = list(executor.map(f, args))

    # Update the fitness scores for each genome
    for genome_id, genome in results:
        for g_id, g in genomes:
            if g_id == genome_id:
                g.fitness = genome.fitness


def run_neat(config_file):
    config = Config(
        neat.DefaultGenome, 
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet, 
        neat.DefaultStagnation,
        config_file,
        )

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    # p.add_reporter(neat.StatisticsReporter())

    # Run for up to 50 generations.
    winner: DefaultGenome = p.run(eval_genomes, 100)
    print(print(f"Winner: {winner.fitness}"))

    import pickle
    with open("best.pkl", 'wb') as f:
        pickle.dump(winner, f)

    # show final stats
    # print(f'\nBest genome:\n{type(winner)}')


if __name__ == '__main__':
    from os import path

    config_path = path.join(path.dirname(__file__), 'config-feedforward.txt')
    run_neat(config_path)