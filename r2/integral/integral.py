def f(x):
    return x**2 + 1


a = 0
b = 2
n = 10_000
dx = (b - a) / n

x = a
area = 0

for i in range(n):
    # rect = f(x) * dx
    rect = (f(x) + f(x + dx)) * dx / 2
    area += rect
    x += dx

print(area)
