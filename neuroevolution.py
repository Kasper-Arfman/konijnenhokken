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




def eval_genome():
    


    users = [
    BotUser(1, strategy),
    ]

    game = Engine(users)
    game.play(1000)