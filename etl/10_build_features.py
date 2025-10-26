#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import numpy as np

def build_features(users_csv, events_csv, out_csv):
    users = pd.read_csv(users_csv, parse_dates=["signup_date","last_active_date"], infer_datetime_format=True)
    events = pd.read_csv(events_csv, parse_dates=["event_timestamp"], infer_datetime_format=True)

    # Alinear tipos de user_id
    if users["user_id"].dtype != events["user_id"].dtype:
        events["user_id"] = events["user_id"].astype(users["user_id"].dtype, errors="ignore")

    # Crear campo de fecha derivado
    events["event_date"] = pd.to_datetime(events["event_timestamp"], errors="coerce").dt.date

    # Conteo de eventos por tipo (pivot)
    if "event_type" in events.columns:
        ev_pivot = (
            events
            .pivot_table(index="user_id", columns="event_type", values="event_uuid", aggfunc="count", fill_value=0)
            .add_prefix("ev_")
            .reset_index()
        )
    else:
        ev_pivot = events.groupby("user_id").size().reset_index(name="ev_count")

    # Días activos
    active_days = (
        events.dropna(subset=["event_date"])
        .groupby("user_id")["event_date"]
        .nunique()
        .reset_index(name="active_days")
    )

    # Sesiones si existe session_id
    if "session_id" in events.columns:
        sessions = (
            events[~events["session_id"].isna()]
            .groupby(["user_id","session_id"]).size().reset_index(name="events_per_session")
        )
        sessions_agg = (
            sessions.groupby("user_id")
            .agg(sessions=("session_id","nunique"),
                 avg_events_per_session=("events_per_session","mean"))
            .reset_index()
        )
    else:
        sessions_agg = pd.DataFrame(columns=["user_id","sessions","avg_events_per_session"])

    # Merge de todo
    feat = users[["user_id","signup_date","last_active_date","country","device","language","subscription_type"]].copy()
    for part in [ev_pivot, active_days, sessions_agg]:
        if not part.empty:
            feat = feat.merge(part, on="user_id", how="left")

    # Ratios derivados
    for a,b in [("ev_play","ev_open"),("ev_pause","ev_play"),("ev_next","ev_play")]:
        if a in feat.columns and b in feat.columns:
            denom = feat[b].replace(0,np.nan)
            feat[f"ratio_{a}_{b}"] = (feat[a] / denom).fillna(0.0)

    # Engagement score inicial (ponderado simple)
    components = [c for c in ["ev_play","ev_pause","ev_next","active_days","sessions"] if c in feat.columns]
    if components:
        feat["engagement_score"] = feat[components].fillna(0).apply(
            lambda r: (
                1.0*r.get("ev_play",0) +
                0.5*r.get("ev_pause",0) +
                1.2*r.get("ev_next",0) +
                3.0*r.get("active_days",0) +
                2.0*r.get("sessions",0)
            ),
            axis=1
        )

    # Completar valores nulos
    for c in feat.columns:
        if feat[c].dtype.kind in "if":
            feat[c] = feat[c].fillna(0)
        elif feat[c].dtype == "O":
            feat[c] = feat[c].fillna("unknown")

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    feat.to_csv(out_csv, index=False)
    print(f"Archivo generado: {out_csv}")
    print(f"Filas: {len(feat)} columnas: {len(feat.columns)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users_csv", required=True, help="Ruta al CSV de usuarios limpios")
    ap.add_argument("--events_csv", required=True, help="Ruta al CSV de eventos limpios")
    ap.add_argument("--out_csv", required=True, help="Ruta de salida del CSV de features")
    args = ap.parse_args()

    build_features(args.users_csv, args.events_csv, args.out_csv)

if __name__ == "__main__":
    main()
