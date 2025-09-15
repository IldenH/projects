# side 79 og 80 kraft 1, eksempel 3-9

import numpy as np
import matplotlib.pyplot as plt

n = 1000
T = 3  # sekunder
t = np.linspace(0, T, n)
dt = T / n

s = np.zeros(n)
v = np.zeros(n)
a = np.zeros(n)

m = 0.200  # kg
g = 9.81  # m/s^2
k = 0.01  # N/(m/s)^2
v[0] = 10  # m/s

for i in range(n - 1):
    G = -m * g
    L = -k * v[i] * abs(v[i])
    F_sum = L + G
    a[i] = F_sum / m
    v[i + 1] = v[i] + a[i] * dt
    s[i + 1] = s[i] + v[i + 1] * dt

plt.figure(1)
plt.grid()
plt.title("Posisjon")
plt.xlabel("$t$ / s")
plt.ylabel("$s$ / m")
plt.plot(t, s, label="k = %.2f" % k)
plt.legend()

plt.figure(2)
plt.grid()
plt.title("Fart")
plt.xlabel("$t$ / s")
plt.ylabel("$v$ / (m/s)")
plt.plot(t, v, label="k = %.2f" % k)
plt.legend()


plt.figure(3)
plt.grid()
plt.title("Akselerasjon")
plt.xlabel("$t$ / s")
plt.ylabel("$a$ / (m/s$^2$)")
plt.plot(t[:-1], a[:-1], label="k = %.2f" % k)
plt.legend()

plt.show()
