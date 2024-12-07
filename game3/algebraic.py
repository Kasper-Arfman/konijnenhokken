"""
4/6: f(x+1)
1/6: f(x+5)
1/6: 0
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.optimize import minimize
# np.set_printoptions(precision=2)
from functools import cache

def img_to_surface(lena: np.ndarray):
    xx, yy = np.mgrid[0:lena.shape[0], 0:lena.shape[1]]
    fig = plt.figure()
    ax = fig.add_subplot(projection = '3d')
    ax.plot_surface(xx, yy, lena ,rstride=1, cstride=1, cmap=plt.cm.gray,
            linewidth=0)
    plt.show()

p = 5/6  # rabbit
q = 1 - p  # no rabbit

# Transfer probabilities
DP = np.array([
    # s0   s1 (to)
    [p*p, 2*p*q], # s0
    [  p,     0], # s1 (from)
])

# Transfer scores
DV = np.array([
    [2, 1],
    [1, 0],
])

N_STATES = DP.shape[0]
N_SCORES = 50
V = np.arange(N_SCORES)  # Scores to test

@cache
def expected_result(T: tuple[int]):
    """
    S[i, x]: Survival probability to state i with a score of x
    """
    S = np.zeros((N_STATES, N_SCORES)); S[0, 0] = 1
    for s_f in range(N_STATES):
        for v_f in V:
            for s_i, dv in enumerate(DV[:, s_f]):
                v_i = v_f - dv
                if 0 <= v_i < int(T[s_i]):
                    S[s_f, v_f] += S[s_i, v_i] * DP[s_i, s_f]

    expected_score = 0
    for i, t in enumerate(T):
        S[i, :int(t)] = 0
        expected_score += S[i]@V
    return expected_score


def objective(T):
    """Bilinear interpolation"""
    T = np.array(T)
    w = T%1
    v = 1 - w
    p = np.floor(T)
    q = p + 1
    return -sum((
        v[0]*v[1]*expected_result((p[0], p[1])),
        v[0]*w[1]*expected_result((p[0], q[1])),
        w[0]*v[1]*expected_result((q[0], p[1])),
        w[0]*w[1]*expected_result((q[0], q[1])),
        ))


y = np.zeros((N_SCORES, N_SCORES))
for t1, row in enumerate(y):
    for t2, val in enumerate(row):
        y[t1, t2] = objective(tuple((t1, t2)))
img_to_surface(y)