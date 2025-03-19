import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
import sys


def modell(t: float, a: float, b: float) -> float:
    return a * t + b


def main():
    # 7.25
    x = [0, 1, 2, 3, 4]
    y = [20, 31, 43, 55, 66]

    koeffisienter, kovarians = curve_fit(modell, x, y)
    print(f"Koeffisienter: {koeffisienter}")
    print(f"Kovarians: {kovarians}")

    x_modell = np.linspace(0, 10)
    a, b = koeffisienter
    y_modell = modell(x_modell, a, b)

    plt.plot(x_modell, y_modell, label="Tilpasset modell")
    plt.scatter(x, y, label="Datapunkter")
    plt.xlabel("minutter")
    plt.ylabel("grader celsius")
    plt.legend()
    plt.show()


if __name__ == "__main__" and not sys.flags.interactive:
    main()
