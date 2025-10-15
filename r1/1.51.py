import matplotlib.pyplot as plt

N = lambda t: 20000 * 1.40**t

x = [0, 1, 2, 3, 4, 5]
y = []

for i in x:
    y.append(N(i))

plt.plot(x, y)
plt.yscale("log")
plt.show()
