from scipy import constants


def stoppelengde(m: int):
    v = 30 / 3.6  # m/s
    # m = 100 # kg
    mu = 0.08
    k = 0.3
    s = 0

    t = 0
    dt = 0.01

    G = constants.g * m
    N = G
    R = mu * N

    while v > 0:
        L = k * v**2
        F = -(R + L)
        a = F / m
        v += a * dt
        s += v * dt
        t += dt

    print(f"Masse {m} kg ==> Stoppelengde: {s:.2f} meter, på {t:.2f} sekunder")


for i in range(1, 100 + 1):
    stoppelengde(i)
