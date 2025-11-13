def f(x):
    return x**3 - 4 * x + 1


a = -1
b = 5
n = 100

x1 = a
x2 = x1 + (b - a) / n

area = 0

for i in range(n):
    midt = (x1 + x2) / 2
    rect = f(midt) * (x2 - x1)
    area += rect
    x1 = x2
    x2 = x1 + (b - a) / n

print(area)
