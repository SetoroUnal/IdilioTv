#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

PRED_PATH = r"data\models\predictions_full.csv"
USERS_PATH = r"data\cleaned\users_clean.csv"
OUT_DIR = r"docs"

def summarize_churn_predictions():
    print("Cargando predicciones y datos de usuario...")
    preds = pd.read_csv(PRED_PATH)
    users = pd.read_csv(USERS_PATH)

    print(f"Predicciones: {len(preds):,} | Usuarios: {len(users):,}")

    # --- Merge básico ---
    df = preds.merge(users, on="user_id", how="left")
    print(f"Merge final: {len(df):,}")

    # --- Distribución general ---
    desc = df["proba_churn"].describe(percentiles=[.1,.25,.5,.75,.9]).round(3)
    print("\nDistribución general de probabilidad de churn:")
    print(desc)

    # --- Tasas promedio por país ---
    churn_country = (
        df.groupby("country")["proba_churn"]
        .mean()
        .reset_index()
        .rename(columns={"proba_churn":"avg_churn_prob"})
        .sort_values("avg_churn_prob", ascending=False)
    )

    # --- Tasas promedio por dispositivo ---
    churn_device = (
        df.groupby("device")["proba_churn"]
        .mean()
        .reset_index()
        .rename(columns={"proba_churn":"avg_churn_prob"})
        .sort_values("avg_churn_prob", ascending=False)
    )

    # --- Tasas promedio por suscripción (si existe) ---
    sub_cols = [c for c in df.columns if "sub" in c.lower()]
    churn_sub = None
    if sub_cols:
        col = sub_cols[0]
        churn_sub = (
            df.groupby(col)["proba_churn"]
            .mean()
            .reset_index()
            .rename(columns={"proba_churn":"avg_churn_prob"})
            .sort_values("avg_churn_prob", ascending=False)
        )

    # --- Guardar resultados ---
    os.makedirs(OUT_DIR, exist_ok=True)
    churn_country.to_csv(os.path.join(OUT_DIR, "churn_by_country.csv"), index=False)
    churn_device.to_csv(os.path.join(OUT_DIR, "churn_by_device.csv"), index=False)
    if churn_sub is not None:
        churn_sub.to_csv(os.path.join(OUT_DIR, "churn_by_subscription.csv"), index=False)

    print("\nPromedio por país:\n", churn_country.head(10).to_string(index=False))
    print("\nPromedio por dispositivo:\n", churn_device.head(10).to_string(index=False))
    if churn_sub is not None:
        print(f"\nPromedio por {col}:\n", churn_sub.to_string(index=False))

    print(f"\nArchivos guardados en: {OUT_DIR}")

if __name__ == "__main__":
    summarize_churn_predictions()
