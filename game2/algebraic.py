"""
4/6: f(x+1)
1/6: f(x+5)
1/6: 0

We rely on dynamic programmin to generate the probabilities of all states

N.B. requires scores stepsize = 1

"""
import numpy as np
import matplotlib.pyplot as plt

p = [0, 4/6, 0, 0, 0, 1/6]
x = np.arange(0, 50)


def expected_result(t):
    """
    S[i]: probability to reach state i
    P[i]: probability to end at state i
    """
    S = np.zeros(x.shape); S[0] = 1
    for i in x:
        if t > i-1 >= 0:
            S[i] += S[i-1] * p[1]
        if t > i-5 >= 0:
            S[i] += S[i-5] * p[5]

    P = S.copy()
    P[:t] = 0  # can't end below t by design
    return P@x


t = np.arange(0, 50)
y = []
for min_score in t:
    y.append(expected_result(min_score))
y = np.array(y)

i_max = np.argmax(y)
t_max = t[i_max]
y_max = y[i_max]
print(f"Time to stop: t={t_max}")  # 9

plt.plot(t, y)
plt.scatter(t_max, y_max, c='r')
plt.show()