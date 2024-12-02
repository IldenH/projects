# Likningen 0,5x^3 = 2x^2 − 1 har tre løsninger.
# a. Tegn en graf og finn tre intervaller som hvert inneholder én av de tre
# løsningene.
# b. Bruk halveringsmetoden flere ganger for å finne de tre løsningene på
# likningen.
# c. Hva skjer om du starter med et intervall som inneholder alle løsningene?
# Forklar.

import matplotlib.pyplot as plt
import numpy as np

f = lambda x: 0.5 * x**3 - (2 * x**2 - 1)

interval = 4
x = np.linspace(-interval, interval, 100)
y = []

for i in x:
    y.append(f(i))

plt.plot(x, y)
# plt.show()

# intervaller som inneholder løsningene
# [-1, 0], [0, 2], [3, 4]
startpunkt = [-1.0, 0.0, 3.0]
sluttpunkt = [0.0, 2.0, 4.0]
nøyaktighet = 0.0001

for i in range(len(startpunkt)):
    if f(startpunkt[i]) * f(sluttpunkt[i]) > 0:
        print("Ingen nullpunkt her")
        quit()

    midtpunkt = (startpunkt[i] + sluttpunkt[i]) / 2

    while abs(f(midtpunkt)) >= nøyaktighet:
        if f(startpunkt[i]) * f(midtpunkt) < 0:
            sluttpunkt[i] = midtpunkt
        else:
            startpunkt[i] = midtpunkt

        midtpunkt = (startpunkt[i] + sluttpunkt[i]) / 2

    nullpunkt = round(midtpunkt, 4)
    print(nullpunkt)
