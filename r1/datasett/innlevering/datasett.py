import pandas as pd
import matplotlib.pyplot as plt

# import numpy as np

brutto = pd.read_csv("bruttoforbruk-elektrisk-kraft.csv", delimiter=";")
# internett = pd.read_csv("tid-brukt-internett-minutter-dag.csv", delimiter=";")

# internett["Minutter brukt til ulike medier en gjennomsnittsdag"] = internett[
#     "Minutter brukt til ulike medier en gjennomsnittsdag"
# ].replace("..", np.nan)

brutto.plot(x="år", y="Bruttoforbruk")
# internett.plot(x="år", y="Minutter brukt til ulike medier en gjennomsnittsdag")

plt.show()
