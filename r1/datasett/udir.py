import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("udir-data.tsv", delimiter="\t")

df.groupby("Fagomraadenavn")[
    "2024-25.Alle eierformer.Alle trinn.Alle kjønn.Antall elever"
].sum().sort_values(ascending=False).head(10).plot(kind="pie", xlabel="", ylabel="")

plt.show()
