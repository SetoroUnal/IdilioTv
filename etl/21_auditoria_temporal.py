#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def auditoria_temporal(events_csv, out_dir="docs"):
    print("Cargando eventos...")
    df = pd.read_csv(events_csv, parse_dates=["event_timestamp", "created_at", "received_at"])

    print(f"Eventos cargados: {len(df):,}")

    # Asegurarse de que las columnas existen
    required_cols = {"event_timestamp", "created_at", "received_at"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Faltan columnas requeridas: {required_cols - set(df.columns)}")

    # Calcular diferencias temporales (en segundos)
    df["delay_event_created"] = (df["created_at"] - df["event_timestamp"]).dt.total_seconds()
    df["delay_created_received"] = (df["received_at"] - df["created_at"]).dt.total_seconds()
    df["delay_event_received"] = (df["received_at"] - df["event_timestamp"]).dt.total_seconds()

    # Resumen estadístico
    resumen = df[["delay_event_created", "delay_created_received", "delay_event_received"]].describe(percentiles=[0.01,0.05,0.5,0.95,0.99])

    # Guardar resumen
    os.makedirs(out_dir, exist_ok=True)
    resumen_path = os.path.join(out_dir, "QA_temporal_resumen.csv")
    resumen.to_csv(resumen_path)
    print(f"Resumen estadístico guardado en {resumen_path}")

    # Gráficos
    plt.figure(figsize=(8,5))
    df["delay_event_created"].hist(bins=100)
    plt.title("Retraso entre event_timestamp y created_at (segundos)")
    plt.xlabel("Segundos de retraso")
    plt.ylabel("Cantidad de eventos")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "delay_event_created.png"))
    plt.close()

    plt.figure(figsize=(8,5))
    df["delay_created_received"].hist(bins=100)
    plt.title("Retraso entre created_at y received_at (segundos)")
    plt.xlabel("Segundos de retraso")
    plt.ylabel("Cantidad de eventos")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "delay_created_received.png"))
    plt.close()

    plt.figure(figsize=(8,5))
    df["delay_event_received"].hist(bins=100)
    plt.title("Retraso total entre event_timestamp y received_at (segundos)")
    plt.xlabel("Segundos de retraso")
    plt.ylabel("Cantidad de eventos")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "delay_event_received.png"))
    plt.close()

    print(f"Gráficos generados en {out_dir}")
    print("Auditoría temporal completada.")

def main():
    auditoria_temporal(events_csv="data/cleaned/events_clean.csv", out_dir="docs")

if __name__ == "__main__":
    main()
