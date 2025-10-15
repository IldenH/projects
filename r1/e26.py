from math import log

f = lambda x: 5 * log(x**3 + 2) + x - 6

start = float(input("Startverdi: "))
slutt = float(input("Sluttverdi: "))
nøyaktighet = 0.0001

midt = (start + slutt) / 2

runder = 0

while abs(f(midt)) >= nøyaktighet:
    if f(start) * f(midt) < 0:
        slutt = midt
    else:
        start = midt

    midt = (start + slutt) / 2

    runder += 1
    print(f"{runder} runder")

print("", round(midt, 4))
