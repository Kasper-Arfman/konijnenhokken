"""
4/6: f(x+1)
1/6: f(x+5)
1/6: 0
"""

import numpy as np
import matplotlib.pyplot as plt

p = 5/6  # rabbit
q = 1 - p  # no rabbit

# Transfer probabilities
P = np.array([
    # s0   s1 (to)
    [p*p, 2*p*q], # s0
    [  p,     0], # s1 (from)
])

# Transfer scores
V = np.array([
    [2, 1],
    [1, 0],
])

def simulate(score, T, state=0):
    roll = np.random.rand()

    ps = np.cumsum(P[state])
    # print(state, ps)
    # exit()
    vs = V[state]

    for new_state, (pi, vi) in enumerate(zip(ps, vs)):
        if roll < pi:
            score += vi
            # print(f"{state} -> {new_state}, {score = :d}")
            state = new_state
            break
    else:
        # print(f'Rolled {roll:.3f} => failed')
        return 0
    
    if score >= T[state]:
        # exit()
        return score

    return simulate(score, T, state)


def main():
    N = 100_000
    t = np.arange(0, 2)
    y = []
    dy = []
    for min_score in t:
        scores = np.array([simulate(0, np.array([26, 19])) for _ in range(N)])

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

if __name__ == "__main__":
    main()