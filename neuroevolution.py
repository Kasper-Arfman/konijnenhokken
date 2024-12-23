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
import pickle

from neat.nn.feed_forward import FeedForwardNetwork
from neat.threaded import ThreadedEvaluator

from src import Engine, BotUser

NUM_TURNS = 1000

Genomes = List[Tuple[int, DefaultGenome]]
hiscore = 0

def eval_genomes(genomes: Genomes, config: Config):
    for genome_id, genome in genomes:
        genome.fitness = eval_genome(genome, config)

def eval_genome(genome: DefaultGenome, config: Config):
    net = FeedForwardNetwork.create(genome, config)
    user = BotUser(net=net, verbose=False)
    game = Engine([user])
    game.play(NUM_TURNS)

    # Evaluate the fitness as the average score
    fitness = game.gs[user].game_score / NUM_TURNS

    global hiscore
    if fitness > hiscore:
        hiscore = fitness
        with open("best.pkl", 'wb') as f:
            pickle.dump(genome, f)
        print(f"New {hiscore = }")

    return fitness

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

    evaluator = eval_genomes
    evaluator = ThreadedEvaluator(3, eval_genome).evaluate

    winner: DefaultGenome = p.run(evaluator, 10_000)
    print(print(f"Winner: {winner.fitness}"))

if __name__ == '__main__':
    from os import path

    config_path = path.join(path.dirname(__file__), 'config-feedforward.txt')
    run_neat(config_path)