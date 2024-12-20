"""

== Allocation Network: which rabbits and which cages should I pick ==
Input:
 - Game Score
 - Turn score
 - Run score
 - rabbits: 2x7
 - cages: 4x7
 - board: 6x7

Output:
 - for rabbits, whether I should take it 2x7
 - for cages, whether I should take it 4x7
 - A mask should be applied to prevent disallowed moves

 
== Continuation Network: should I keep going?
Input:
 - Game Score
 - Turn score
 - Run score
 - rabbits: 2x7
 - cages: 4x7


Output:
 - Decision node (yes or no)



== Fitness evaluation
 - The average score after playing 1000 matches (for now)



"""
import neat
from neat.config import Config
from neat.genome import DefaultGenome
from typing import List, Tuple

from neat.nn.feed_forward import FeedForwardNetwork

from src import Engine, BotUser, BotUI, CommandUI

NUM_TURNS = 1000

Genomes = List[Tuple[int, DefaultGenome]]

def eval_genomes(genomes: Genomes, config: Config):
    """Compute the fitness of every genome and store it in genome.fitness"""

    

    for genome_id, genome in genomes:
        genome.fitness = 0

        # Play the game with each genome 1000 times
        net = FeedForwardNetwork.create(genome, config)
        user = BotUser(genome_id, net=net, ui=None, verbose=False)
        game = Engine([user])
        game.play(NUM_TURNS)

        # Evaluate the fitness as the average score
        genome.fitness = game.gs[user].game_score / NUM_TURNS



        


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