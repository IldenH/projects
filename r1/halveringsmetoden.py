import numpy as np


# f = lambda x: 5 * np.log(x**3 + 2) - 6 + x
f = lambda x: 350 * (1.2) ** x - 756


a = -10
b = 10

feil = 1e-6

m = (a + b) / 2

while abs(f(m)) > feil:
    if f(a) * f(m) > 0:
        a = m
    else:
        b = m

    m = (a + b) / 2


print(f"{m}, {f(m):.0f}")
print(f"Likningen har løsning tilnærmet lik x = {m:.4f}")
