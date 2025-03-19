import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
import sys


def modell(t, a, b, C):
    return C / (1 + a * np.exp(-b * t))


def main():
    # Eksempel 12 kapittel 7
    x = [0, 8, 20, 28, 39, 54, 69, 84, 100]
    y = [1, 21, 1118, 2580, 5107, 6890, 7787, 8223, 8433]

    # x = [1, 2, 3, 4, 5]
    # y = [2.1, 3.9, 6.5, 7.1, 11.0]

    assert len(x) == len(y)

    koeffisienter, kovarians = curve_fit(modell, x, y, p0=[0, 0, 8450])
    print(f"Koeffisienter: {koeffisienter}")
    print(f"Kovarians: {kovarians}")

    x_modell = np.linspace(x[0], x[-1], 1000)
    a, b, C = koeffisienter
    print(f"a: {a}\nb: {b}\nC: {C}")
    y_modell = modell(x_modell, a, b, C)

    plt.plot(x_modell, y_modell, label="Tilpasset modell", color="red")
    plt.scatter(x, y, label="Datapunkter", color="navy")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.show()


if __name__ == "__main__" and not sys.flags.interactive:
    main()
