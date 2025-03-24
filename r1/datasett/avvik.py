import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


data = np.array(
    [
        [4.02, 4.14, 4.0, 3.73, 3.93],
        [2.44, 2.38, 2.77, 2.77, 2.51],
        [
            2.24,
            2.19,
            2.3,
            2.12,
            2.5,
        ],
        [
            2.12,
            1.86,
            1.99,
            1.97,
            2.05,
        ],
    ]
)

lengde = [3, 5, 7, 9]

y_snitt = []
standard_avvik = []
standard_error = []

for y in data:
    n = len(y)
    average = sum(y) / n
    y_snitt.append(average)

    s = np.sqrt(sum((y - average) ** 2) / (n - 1))
    standard_avvik.append(s)

    se = s / np.sqrt(n)
    standard_error.append(se)

y_snitt = np.array(y_snitt)
standard_avvik = np.array(standard_avvik)
standard_error = np.array(standard_error)

print(y_snitt)
print(standard_avvik)
print(standard_error)


# def modell(t: float, a: float, b: float) -> float:
#     return a * t + b


def modell(t: float, a: float, b: float) -> float:
    return a * t**b


koeffisienter, kovarians = curve_fit(modell, lengde, y_snitt)
print(f"Koeffisienter: {koeffisienter}")
print(f"Kovarians: {kovarians}")

x_modell = np.linspace(lengde[0], lengde[-1])
a, b = koeffisienter
y_modell = modell(x_modell, a, b)

plt.plot(x_modell, y_modell, "--")


plt.plot(lengde, y_snitt, "b.")
plt.vlines(lengde, y_snitt - 2 * standard_error, y_snitt + 2 * standard_error, "r")
plt.xlabel("Lengde (cm)")
plt.ylabel("Tid (sekunder)")
plt.show()
