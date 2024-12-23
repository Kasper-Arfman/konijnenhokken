"""
The state space is small enough to compute all states.
Figuring out the run_score is easy. But the roll_score is initially unknown

State | stop | <roll>
0 0 0 |   0  |    ...

Initialize a dictionary with all states and their stop values.

Use this as a policy for both allocation and continuation

Realize that the value of every state depends on my score as well
- Find the states that may exist

"""
import neat
import os
import random
from collections import Counter
from functools import cache
import neat.threaded
from numba import njit

ROUNDS = 1_000
GENERATIONS = 10_000

LOCAL_DIR = os.path.dirname(__file__)

CONFIG = neat.config.Config(
    neat.DefaultGenome, 
    neat.DefaultReproduction,
    neat.DefaultSpeciesSet, 
    neat.DefaultStagnation,
    os.path.join(LOCAL_DIR, 'value.txt'),
    )

def init_states():
    n = 0
    d = {}
    for turn_score in range(100):
        for r1 in range(8):
            for r2 in range(8-r1):
                for c in range(min(8-r1-r2, 5)):
                    d[turn_score, r1, r2, c] = n
                    n += 1
    return d
ID = init_states()  # dict[state -> id]
print(f"ID: {len(ID)} states")

@cache
def possible_states(state: tuple, roll: list):
    turn_score, src_1, src_2, src_c = state
    roll = Counter(roll)

    # Find all the states that can be accessed
    states = set()
    for d1 in range(roll[1]+1):
        for d2 in range(roll[2]+1):
            # Must add atleast one rabbit
            if (d1, d2) == (0, 0):  continue

            # 1: Add only rabbits
            states.add((turn_score, src_1+d1, src_2+d2, src_c))

            # if i took some two's, remove them before checking if I have some
            # The 2 you needed was already used as a rabbit
            tmp = roll.copy()
            tmp[2] -= d2
            if not tmp[2]:  continue


            # 2: Add cages as well
            for dc, cage in enumerate(range(src_c+2, 6), 1):
                if cage not in roll:  break
                # Add this possibility
                states.add((turn_score, src_1+d1, src_2+d2, src_c+dc))

    return states

# @njit
def decide_allocation(state, roll, values: list, ID=ID):
    """Find all the states that can be reached from here
    Pick the one with the largest score.
    """
    states = possible_states(state, tuple(roll))
    if not states:  return None

    best_state, best_val = next(iter(states)), 0
    for state in states:
        val = values[ID[state]]
        if val > best_val:
            best_state, best_val = state, val
    # print(best_state)
    return best_state

# @njit
def decide_continue(state, values: list, ID=ID):
    turn_score, r1, r2, c = state
    stop = turn_score + (r1 + 2*r2) * (c+1)
    roll = values[ID[state]]
    return roll > stop

# @njit
def simulate_game(rounds, values, ID=ID):
    game_score = 0
    for _ in range(rounds):
        state = (0, 0, 0, 0)
        dice_remaining = 7

        while True:
            roll = sorted([random.randint(1, 6) for _ in range(dice_remaining)])
            # print(f"rolled", roll)

            if 1 not in roll and 2 not in roll:
                turn_score, run_score = 0, 0
                # print('died.')
                break

            state = decide_allocation(state, roll, values, ID)
            dice_remaining = 7 - sum(state)

            if not dice_remaining:
                turn_score, r1, r2, c = state
                turn_score += (r1 + 2*r2) * (c+1)
                state = (turn_score, r1, r2, c)

            if not decide_continue(state, values, ID):
                # print('stopped')
                turn_score, r1, r2, c = state
                game_score += turn_score + (r1 + 2*r2) * (c+1)
                break
    return game_score / rounds

def solve_game():
    p = neat.Population(CONFIG)
    p.add_reporter(neat.StdOutReporter(True))
    evaluator = neat.threaded.ThreadedEvaluator(1, eval_genome).evaluate
    winner = p.run(evaluator, GENERATIONS)
    return winner


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = eval_genome(genome, config)

def eval_genome(genome, config):
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    values = net.activate(inputs=[0])

    # print(values[:10])
    # exit()


    fitness = simulate_game(ROUNDS, values)
    return fitness


if __name__ == "__main__":
    solve_game()
    # import numpy as np
    # values = np.random.randint(1, 10, 110)
    # fitness = simulate_game(1, values)
    # print(fitness)