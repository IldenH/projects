import math


def f(x):
    return math.e ** (-x**2)

dx = 0.001

a = 0
b = 2
n = (b - a) / dx

s = 0

for i in range(int(n)):
    r = f(dx * i)
    area = math.pi * r ** 2
    print(r, area)
    s += area * dx

print(s)
