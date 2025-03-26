import csv
import matplotlib.pyplot as plt

data = {}

with open("svalbard-data.csv") as file:
    contents = csv.DictReader(file, delimiter=";")
    for row in contents:
        år = row["Tid(norsk normaltid)"]
        temperatur = row["Middeltemperatur (år)"]

        try:
            temperatur = float(temperatur.replace(",", "."))
        except ValueError:
            continue

        data[år] = temperatur

år = list(data.keys())
temperatur = list(data.values())
plt.plot(år, temperatur)
plt.xticks(range(0, len(år), 3))
plt.xlabel("Årstall")
plt.ylabel("Temperatur")
plt.title("Svalbard temperatur på Hopen stasjon")
plt.legend()
plt.grid()
plt.show()
