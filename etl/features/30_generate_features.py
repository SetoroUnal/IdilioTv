#!/usr/bin/env python3
import pandas as pd
import os

def generate_features(users_csv, events_csv, out_csv):
    # --- Cargar datos ---
    users = pd.read_csv(users_csv, parse_dates=["signup_date", "last_active_date"])
    events = pd.read_csv(events_csv, parse_dates=["event_timestamp"])

    print(f"Usuarios cargados: {len(users):,}")
    print(f"Eventos cargados: {len(events):,}")

    # --- Feature 1: Recencia (último evento) ---
    max_date = events["event_timestamp"].max()
    recencia = (
        events.groupby("user_id")["event_timestamp"]
        .max()
        .reset_index()
        .rename(columns={"event_timestamp": "last_event"})
    )
    recencia["recency_days"] = (max_date - recencia["last_event"]).dt.days
    recencia.drop(columns=["last_event"], inplace=True)

    # --- Feature 2: Frecuencia (total de eventos) ---
    frecuencia = (
        events.groupby("user_id")["event_uuid"]
        .count()
        .reset_index()
        .rename(columns={"event_uuid": "event_count"})
    )

    # --- Feature 3: Diversidad de eventos ---
    diversidad = (
        events.groupby("user_id")["event_type"]
        .nunique()
        .reset_index()
        .rename(columns={"event_type": "unique_event_types"})
    )

    # --- Unir todas las métricas ---
    features = (
        users.merge(frecuencia, on="user_id", how="left")
        .merge(recencia, on="user_id", how="left")
        .merge(diversidad, on="user_id", how="left")
    )

    # --- Rellenar nulos ---
    features.fillna(
        {"event_count": 0, "recency_days": 9999, "unique_event_types": 0},
        inplace=True,
    )

    # --- Guardar resultado ---
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    features.to_csv(out_csv, index=False)
    print(f"\nFeature store guardada en {out_csv}")
    print(f"Columnas generadas: {list(features.columns)}")

def main():
    generate_features(
        users_csv="data/cleaned/users_clean.csv",
        events_csv="data/cleaned/events_clean.csv",
        out_csv="data/features/user_features.csv",
    )

if __name__ == "__main__":
    main()
