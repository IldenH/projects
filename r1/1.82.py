f = lambda x: 3 * 2 ** (x - 1) - 4

startpunkt = [0.0]
sluttpunkt = [2.0]
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
