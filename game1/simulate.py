# f(x):
# 2/3:    f(x+2) points
# 1/3:    0 points


import numpy as np

# We only get the choice to stop, if we hit f(x+2)
# The only thing to consider is x
# lets investigate how the expected value depends on the threshold for going
def simulate(score, min_score=0):
    roll = np.random.rand()
    if roll < 5/6:
        score += 1
        if score >= min_score:
            return score
        return simulate(score, min_score)
    return 0

N = 100_000


min_scores = np.arange(1, 50)
means = []
std_errs = []

for min_score in min_scores:
    scores = np.array([simulate(0, min_score) for _ in range(N)])

    avg = np.mean(scores)
    std = np.std(scores) / np.sqrt(len(scores))

    means.append(avg)
    std_errs.append(std)

means = np.array(means)
std_errs = np.array(std_errs)

import matplotlib.pyplot as plt
plt.plot(min_scores, means)
plt.plot(min_scores, means-std_errs, 'k--')
plt.plot(min_scores, means+std_errs, 'k--')
plt.show()
# Setting the threshold at 5 maximizes the score!