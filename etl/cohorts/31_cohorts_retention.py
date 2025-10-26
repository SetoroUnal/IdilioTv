#!/usr/bin/env python3
import pandas as pd
import os

def build_retention_cohorts(users_csv, events_csv, out_csv):
    print("Cargando datasets...")
    users = pd.read_csv(users_csv, parse_dates=["signup_date"])
    events = pd.read_csv(events_csv, parse_dates=["event_timestamp"])

    print(f"Usuarios cargados: {len(users):,}")
    print(f"Eventos cargados: {len(events):,}")

    # --- Cohorte: mes de registro ---
    users["cohort_month"] = users["signup_date"].dt.to_period("M")

    # --- Actividad: mes del evento ---
    events["event_month"] = events["event_timestamp"].dt.to_period("M")

    # --- Unir usuarios y eventos ---
    merged = events.merge(
        users[["user_id", "cohort_month", "signup_date"]],
        on="user_id",
        how="left"
    )

    # --- Retención por cohorte mensual ---
    retention = (
        merged.groupby(["cohort_month", "event_month"])["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "active_users"})
    )

    # --- Tamaño de cohorte ---
    cohort_sizes = users.groupby("cohort_month")["user_id"].nunique().reset_index()
    cohort_sizes = cohort_sizes.rename(columns={"user_id": "cohort_size"})

    # --- Unir tamaños ---
    retention = retention.merge(cohort_sizes, on="cohort_month")
    retention["retention_rate"] = retention["active_users"] / retention["cohort_size"]

    # --- Guardar resultado de cohortes ---
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    retention.to_csv(out_csv, index=False)
    print(f"\n Cohortes de retención guardadas en {out_csv}")

    # --- Validar presencia de signup_date ---
    if "signup_date" not in merged.columns:
        raise ValueError("La columna signup_date no existe en el dataset unificado (merge).")

    # --- Retención D7 y D30 ---
    print("\nCalculando métricas D7, D30 y churn...")
    merged["days_since_signup"] = (merged["event_timestamp"] - merged["signup_date"]).dt.days

    d7 = merged[merged["days_since_signup"] <= 7].groupby("user_id").size().reset_index(name="events_D7")
    d30 = merged[merged["days_since_signup"] <= 30].groupby("user_id").size().reset_index(name="events_D30")

    churn = merged.groupby("user_id")["days_since_signup"].max().reset_index()
    churn["churn_30d"] = churn["days_since_signup"].apply(lambda x: 0 if pd.notnull(x) and x > 30 else 1)

    # --- Unir métricas ---
    metrics = (
        users.merge(d7, on="user_id", how="left")
        .merge(d30, on="user_id", how="left")
        .merge(churn[["user_id", "churn_30d"]], on="user_id", how="left")
    )

    metrics.fillna({"events_D7": 0, "events_D30": 0, "churn_30d": 1}, inplace=True)

    # --- Guardar ---
    out_metrics = out_csv.replace("retention_cohorts.csv", "user_retention_metrics.csv")
    metrics.to_csv(out_metrics, index=False)
    print(f" Métricas de retención individuales guardadas en {out_metrics}")

    print("\nEjecución completada correctamente.")

def main():
    build_retention_cohorts(
        users_csv="data/cleaned/users_clean.csv",
        events_csv="data/cleaned/events_clean.csv",
        out_csv="data/cohorts/retention_cohorts.csv"
    )

if __name__ == "__main__":
    print("Iniciando script de cohortes y retención...\n")
    main()
