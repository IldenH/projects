import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.optimize import curve_fit
import numpy as np

END_YEAR = 2025 + 30

# https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series
climate = pd.read_csv("climate-change.csv", delimiter=",")
climate["Year"] = pd.to_datetime(climate["Year"], format="%Y")

# https://www.kaggle.com/datasets/somesh24/sea-level-change
sea_level = pd.read_csv("sea-levels.csv", delimiter=",")
sea_level["Time"] = pd.to_datetime(sea_level["Time"], format="%Y-%m-%d")


def modell(t, a, b, c):
    return a * t**2 + b * t + c


def make_modell(x, y):
    koeffisienter, kovarians = curve_fit(modell, x, y)
    x_modell = np.linspace(x[0], END_YEAR)
    a, b, c = koeffisienter
    y_modell = modell(x_modell, a, b, c)

    return (x_modell, y_modell)


fig, ax1 = plt.subplots()

ax1.plot(
    climate["Year"],
    climate["Anomaly"],
    color="red",
    label="Climate Change Anomaly Celsius",
)
ax1.tick_params(axis="y", labelcolor="red")
ax1.set_ylabel("Klimaendringer avvik", color="red")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"{val:.1f}°C"))


x = climate["Year"].dt.year.values.astype(int)
y = climate["Anomaly"]
x_modell, y_modell = make_modell(x, y)

ax1.plot(
    pd.to_datetime(x_modell, format="%Y"),
    y_modell,
    label="Tilpasset modell",
    color="orange",
    linestyle="--",
)
# ax1.scatter(pd.to_datetime(x, format="%Y"), y, label="Datapunkter", color="red")

ax2 = ax1.twinx()
ax2.plot(
    sea_level["Time"], sea_level["GMSL"], color="blue", label="Global Mean Sea Level"
)
ax2.tick_params(axis="y", labelcolor="blue")
ax2.set_ylabel("Havnivå", color="blue")
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"{val:.1f}mm"))

x = sea_level["Time"].dt.year.values.astype(int)
y = sea_level["GMSL"]
x_modell, y_modell = make_modell(x, y)

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
fig.legend(loc="lower right")
ax1.grid(color="pink")
ax2.grid(color="lightblue")
plt.show()
