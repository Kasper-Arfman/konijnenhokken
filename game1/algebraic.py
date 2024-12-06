"""Compute the expected score as a function of t"""
import numpy as np

p = 5/6
t = np.arange(1, 50)
y = t*p**t

i_max = np.argmax(y)
t_max = t[i_max]
y_max = y[i_max]
print(f"Time to stop: t={t_max}")

import matplotlib.pyplot as plt
plt.plot(t, y)
plt.scatter(t_max, y_max)
plt.show()

