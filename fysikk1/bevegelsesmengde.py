import numpy as np
import matplotlib.pyplot as plt

m = 1500  # kg
v = 40 * 3.6  # m/s
n = 50
t = np.linspace(0, 5, n)
p = np.zeros(n) + m * v
f = np.zeros(n)

for i in range(1, n):
    if t[i] > 1 and t[i] <= 4:
        F = 36_000  # N
        p[i] = p[i - 1] + F * (t[i] - t[i - 1])
        f[i] = F
    else:
        p[i] = p[i - 1]
        f[i] = 0

plt.figure()
plt.plot(t, p / 1000)
plt.title("Bevegelsesmengde")
plt.xlabel("$t$ / s")
plt.ylabel("$p$ / $10^3$ kg m/s")
plt.grid()

plt.figure()
plt.plot(t, f / 1000)
plt.title("Kraft")
plt.xlabel("$t$ / s")
plt.ylabel("$F$ / $10^3$ N")
plt.grid()
plt.show()
