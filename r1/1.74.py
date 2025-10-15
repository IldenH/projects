from math import log10

# f = lambda x: log10(x + 2) + x - 2
f = lambda x: 350 * 1.2**x - 756

start = float(input("Startverdi: "))
print(f(start))
slutt = float(input("Sluttverdi: "))
print(f(slutt))
nøyaktighet = 0.0001


if f(start) * f(slutt) > 0:
    print("Ingen nullpunkt her")
    quit()

midt = (start + slutt) / 2

while abs(f(midt)) >= nøyaktighet:
    if f(start) * f(midt) < 0:
        slutt = midt
    else:
        start = midt

    midt = (start + slutt) / 2

nullpunkt = round(midt, 4)
print(nullpunkt)
