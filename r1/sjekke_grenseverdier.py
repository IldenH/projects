def f(x):
    return 2 * (x**2 - 16) / (x - 4)


print("Sjekker ovenfra:")
print("x \t \t f(x)")

for i in range(1, 7):
    dx = 10 ** (-i)  # delta x forandring. mindre og mindre
    x = 4 + dx
    y = round(f(x), 7)
    print(f"{x} \t \t {y}")


print("\nSjekker nedenfra:")
print("x \t \t f(x)")

for i in range(1, 7):
    dx = 10 ** (-i)  # delta x forandring. mindre og mindre
    x = 4 - dx
    y = round(f(x), 7)
    print(f"{x} \t \t {y}")
