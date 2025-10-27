#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def segment_users(
    features_csv="data/features/model_data.csv",
    out_data="data/analytics/user_clusters.csv",
    out_summary="docs/cluster_summary.csv",
    out_elbow="docs/segmentation_elbow.png",
    out_silhouette="docs/segmentation_silhouette.png"
):
    print("Cargando dataset de features...")
    df = pd.read_csv(features_csv)
    if "user_id" not in df.columns:
        raise ValueError("No se encontró la columna 'user_id' en el dataset.")

    print(f"Usuarios cargados: {df.shape[0]:,} | Variables: {df.shape[1]}")

    # --- Selección de columnas numéricas relevantes ---
    candidate_vars = [
        "event_count", "recency_days", "unique_event_types",
        "credits_purchased", "credits_spent", "views",
        "avg_watch_time_sec", "sessions_7d"
    ]
    vars_used = [v for v in candidate_vars if v in df.columns]
    if not vars_used:
        raise ValueError("No se encontraron columnas numéricas relevantes en el dataset.")

    X = df[vars_used].fillna(0)

    # --- Escalado ---
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- Evaluar número óptimo de clusters ---
    print("Evaluando número de clusters...")
    inertias, silhouettes = [], []
    k_values = range(2, 10)
    for k in k_values:
        km = KMeans(n_clusters=k, random_state=42)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    # --- Graficar métricas ---
    os.makedirs(os.path.dirname(out_elbow), exist_ok=True)
    plt.figure()
    plt.plot(k_values, inertias, marker="o")
    plt.title("Elbow Method - KMeans")
    plt.xlabel("Número de clusters (k)")
    plt.ylabel("Inercia")
    plt.savefig(out_elbow, bbox_inches="tight")
    plt.close()

    plt.figure()
    plt.plot(k_values, silhouettes, marker="o")
    plt.title("Silhouette Score por k")
    plt.xlabel("Número de clusters (k)")
    plt.ylabel("Silhouette Score")
    plt.savefig(out_silhouette, bbox_inches="tight")
    plt.close()

    # --- Elegir k óptimo (máximo silhouette) ---
    k_opt = k_values[int(np.argmax(silhouettes))]
    print(f"Mejor número de clusters según Silhouette: k = {k_opt}")

    # --- Entrenar modelo final ---
    kmeans = KMeans(n_clusters=k_opt, random_state=42)
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # --- Guardar resultados ---
    os.makedirs(os.path.dirname(out_data), exist_ok=True)
    df.to_csv(out_data, index=False)
    print(f"Asignaciones de cluster guardadas en: {out_data}")

    # --- Resumen estadístico ---
    cluster_summary = (
        df.groupby("cluster")[vars_used]
        .mean()
        .round(2)
        .reset_index()
        .sort_values("cluster")
    )
    cluster_summary["user_count"] = df["cluster"].value_counts().sort_index().values
    cluster_summary["pct_total"] = (cluster_summary["user_count"] / len(df) * 100).round(2)
    cluster_summary.to_csv(out_summary, index=False)
    print(f"Resumen de clusters guardado en: {out_summary}")

    print("\n--- Segmentación completada ---")
    print(cluster_summary)

def main():
    segment_users()

if __name__ == "__main__":
    main()
