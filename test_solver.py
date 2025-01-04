"""
Every time a state is reached, keep track of what result is achieved

if I score points, increase the value estimate

if I lose my points, decrease the value estimate


Implement this via a running average



"""
import numpy as np

memory = 100

scores = []  # keep track of the last 100 times I visited this state

estimate = np.average(scores)



# make random moves to get initial values

# play the game using this strategy, but:
# - also make moves that have less value (temperature parameter)
# - gradually decrease the temperature






