import numpy as np
import matplotlib.pyplot as plt


def derivert(f, x, h=1e-4):
    return (f(x + h) - f(x)) / h


def derivert_newton(f, x, h=1e-4):
    return (f(x + h) - f(x - h)) / 2 * h


f = lambda x: 3 * x**2 - 2 * x + 1
# f = lambda x: np.sqrt(np.log(x))

a = 3

df = derivert(f, a)
df_newton = derivert_newton(f, a)
print(f"f'({a}) = {df:.4f}")
print(f"f'({a}) = {df_newton:.4f}")

# Plotting
x = np.linspace(-1, 4, 1000)
y = f(x)
df = derivert_newton(f, x)
plt.plot(x, y, color="black", label="f(x)")
plt.plot(x, df, color="red", label="f'(x)")
plt.axhline(color="grey")
plt.axvline(color="grey")
plt.legend()
plt.grid()
plt.show()
