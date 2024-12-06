"""
4/6: f(x+1)
1/6: f(x+5)
1/6: 0
"""

import numpy as np
import matplotlib.pyplot as plt

p1 = 4/6
p2 = 1/6

def simulate(score, min_score=0):
    roll = np.random.rand()
    if roll < p1:
        score += 1
    elif roll < p1 + p2:
        score += 5
    else:
        return 0
    
    if score >= min_score:
        return score

    return simulate(score, min_score)

N = 100_000


t = np.arange(1, 50)
y = []
dy = []
for min_score in t:
    scores = np.array([simulate(0, min_score) for _ in range(N)])

    avg = np.mean(scores)
    std = np.std(scores) / np.sqrt(len(scores))

    y.append(avg)
    dy.append(std)
y = np.array(y)
dy = np.array(dy)

i_max = np.argmax(y)
t_max = t[i_max]
y_max = y[i_max]
print(f"Time to stop: t={t_max}")  # 9

plt.plot(t, y)
plt.plot(t, y-dy, 'k--')
plt.plot(t, y+dy, 'k--')
plt.scatter(t_max, y_max, c='r')
plt.show()