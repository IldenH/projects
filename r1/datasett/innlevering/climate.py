import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np

YEARS_IN_FUTURE = 30

# https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series
climate = pd.read_csv("climate-change.csv", delimiter=",")
climate["Year"] = pd.to_datetime(climate["Year"], format="%Y")

# https://www.kaggle.com/datasets/somesh24/sea-level-change
sea_level = pd.read_csv("sea-levels.csv", delimiter=",")
sea_level["Time"] = pd.to_datetime(sea_level["Time"], format="%Y-%m-%d")


def modell(t, a, b, c):
    return a * t**2 + b * t + c


x = climate["Year"].dt.year.values.astype(int)
y = climate["Anomaly"].values

koeffisienter, kovarians = curve_fit(modell, x, y)
x_modell = np.linspace(x[0], x[-1] + YEARS_IN_FUTURE)
a, b, c = koeffisienter
y_modell = modell(x_modell, a, b, c)

fig, ax1 = plt.subplots()

ax1.plot(
    climate["Year"],
    climate["Anomaly"],
    color="red",
    label="Climate Change Anomaly Celsius",
)
ax1.tick_params(axis="y", labelcolor="red")
ax1.set_ylabel("Grader celsius")

ax1.plot(
    pd.to_datetime(x_modell, format="%Y"),
    y_modell,
    label="Tilpasset modell",
    color="orange",
    linestyle="--",
)
ax1.scatter(pd.to_datetime(x, format="%Y"), y, label="Datapunkter", color="red")

ax2 = ax1.twinx()
ax2.plot(
    sea_level["Time"], sea_level["GMSL"], color="blue", label="Global Mean Sea Level"
)
ax2.tick_params(axis="y", labelcolor="blue")
ax2.set_ylabel("Sjønivå millimeter")

x = sea_level["Time"].dt.year.values.astype(int)
y = sea_level["GMSL"].values

koeffisienter, kovarians = curve_fit(modell, x, y)
x_modell = np.linspace(x[0], x[-1] + YEARS_IN_FUTURE)
a, b, c = koeffisienter
y_modell = modell(x_modell, a, b, c)

ax2.plot(
    pd.to_datetime(x_modell, format="%Y"),
    y_modell,
    label="Tilpasset modell",
    color="purple",
    linestyle="--",
)
# ax2.scatter(pd.to_datetime(x, format="%Y"), y, label="Datapunkter", color="blue")

plt.title("Klimaendringer og havnivå")
ax1.set_xlabel("Årstall")

plt.legend()
ax1.legend()
ax2.legend()
# plt.tight_layout()
plt.grid()
plt.show()
