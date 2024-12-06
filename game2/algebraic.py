"""
4/6: f(x+1)
1/6: f(x+5)
1/6: 0

We rely on dynamic programmin to generate the probabilities of all states

N.B. requires scores stepsize = 1

"""
import numpy as np
import matplotlib.pyplot as plt

v = np.arange(0, 50)  # score outcomes to consider
dv = [1, 5]  # scores that may be gained
p = [4/6, 1/6]  # probability to gain dv[i] points

def expected_result(t):
    # Survival probability
    P = np.zeros(v.shape); P[0] = 1
    for vi in v:
        for dvi, pi in zip(dv, p):
            if 0 <= vi-dvi < t:
                P[vi] += P[vi-dvi] * pi

    # Destination probability
    P[:t] = 0  # can't end up below t
    expected_score = P@v
    return expected_score


t = np.arange(0, 50)
y = []
for min_score in t:
    y.append(expected_result(min_score))
y = np.array(y)

i_max = np.argmax(y)
t_max = t[i_max]
y_max = y[i_max]
print(f"Result: play until score={t_max}")  # 9

plt.plot(t, y)
plt.scatter(t_max, y_max, c='r')
plt.show()