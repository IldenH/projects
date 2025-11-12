from scipy import constants

m = 0.0055
g = constants.g
k = 0.47
s = 0
v = 0
t = 0
dt = 0.001

while s < 20 / 100:
    G = m * g
    L = k * v
    a = (G - L) / m
    v += a * dt
    s += v * dt
    t += dt

print(t)
