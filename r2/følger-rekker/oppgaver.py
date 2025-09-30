import functools

def f(n: int, n_1: int, k: int) -> int:
    return n_1 * k ** (n - 1)

for i in range(1, 20 + 1):
    print(f(i, 3, 2))

i = 1
while f(i, 2, 5) <= 10_000:
    print(f(i, 2, 5))
    i += 1

@functools.lru_cache()
def f2(n):
    if n == 1:
        return 2
    return 2 * f2(n - 1) + 1

for i in range(1, 10 + 1):
    print(f2(i))

# 2,1,3,4,7,11,18,...,a_n
@functools.lru_cache()
def lucas(n):
    if n in {0, 1}:
        return 2
    if n == 2:
        return 1
    return lucas(n - 1) + lucas(n - 2)

for i in range(1, 10 + 1):
    print(lucas(i))
