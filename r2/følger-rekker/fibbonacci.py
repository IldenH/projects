# a1 = 1
# a2 = 1
# print(a1)
#
# for i in range(10 - 1):
#     print(a2)
#     minne = a2
#     a2 = a1 + a2
#     a1 = minne

import functools

@functools.lru_cache()
def f(n):
    if n in {0,1}:
        return 1
    return f(n-1) + f(n-2)

for i in range(1, 1000 + 1):
    print(f(i))
