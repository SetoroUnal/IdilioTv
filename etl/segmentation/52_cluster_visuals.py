## BoxPlots
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("data/analytics/user_clusters.csv")

metrics = ["event_count", "credits_purchased", "credits_spent", "views", "avg_watch_time_sec"]
for col in metrics:
    sns.boxplot(x="cluster", y=col, data=df)
    plt.title(f"Distribución de {col} por cluster")
    plt.savefig(f"docs/cluster_boxplot_{col}.png", bbox_inches="tight")
    plt.close()
## PCA 2D
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

X = df.select_dtypes(include=["float64", "int64"]).drop(columns=["cluster"])
X_scaled = StandardScaler().fit_transform(X)

pca = PCA(n_components=2)
pca_result = pca.fit_transform(X_scaled)
df["pca1"], df["pca2"] = pca_result[:, 0], pca_result[:, 1]

plt.figure(figsize=(6, 6))
sns.scatterplot(data=df, x="pca1", y="pca2", hue="cluster", palette="Set2")
plt.title("Separación visual de clusters (PCA 2D)")
plt.savefig("docs/cluster_pca_scatter.png", bbox_inches="tight")
plt.close()
