import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series
climate = pd.read_csv("climate-change.csv", delimiter=",")
climate["Year"] = pd.to_datetime(climate["Year"], format="%Y")
climate = climate.rename(columns={"Anomaly": "Temperature"})
climate["Year"] = climate["Year"].dt.year

# https://www.kaggle.com/datasets/somesh24/sea-level-change
sea_level = pd.read_csv("sea-levels.csv", delimiter=",")
sea_level["Time"] = pd.to_datetime(sea_level["Time"], format="%Y-%m-%d")
sea_level = sea_level.rename(columns={"GMSL": "Sea_Level"})

sea_level["Sea_Level"] = sea_level["Sea_Level"] - sea_level.iloc[0]["Sea_Level"]
sea_level["Year"] = sea_level["Time"].dt.year


sea_level_yearly = sea_level.sort_values("Time").groupby("Year").first().reset_index()

merged = pd.merge(climate, sea_level_yearly, on="Year", how="inner")
merged.dropna()

x = merged["Temperature"]
y = merged["Sea_Level"]

plt.title("Klimaendringer og havnivå")
plt.xlabel("Temperatur")
plt.ylabel("Havnivå")

plt.scatter(merged["Temperature"], merged["Sea_Level"])
slope, intercept = np.polyfit(x, y, 1)
trendline = slope * x + intercept
plt.plot(x, trendline, color="red")

ax = plt.gca()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"{val:.1f}°C"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"{val:.1f}mm"))

plt.grid()
plt.show()
