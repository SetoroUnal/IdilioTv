#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os
from datetime import datetime

def auditoria_calidad(users_csv, events_csv, out_md):
    users = pd.read_csv(users_csv, parse_dates=["signup_date", "last_active_date"])
    events = pd.read_csv(events_csv, parse_dates=["event_timestamp", "created_at", "received_at"])

    total_users = len(users)
    total_events = len(events)

    resumen = []

    # --- 1. Completitud ---
    resumen.append(("Usuarios sin user_id", users["user_id"].isna().sum()))
    resumen.append(("Eventos sin event_uuid", events["event_uuid"].isna().sum()))
    resumen.append(("Eventos sin user_id", events["user_id"].isna().sum()))

    # --- 2. Unicidad ---
    resumen.append(("Duplicados user_id", total_users - users["user_id"].nunique()))
    resumen.append(("Duplicados event_uuid", total_events - events["event_uuid"].nunique()))

    # --- 3. Integridad referencial ---
    usuarios_eventos_validos = events["user_id"].isin(users["user_id"]).sum()
    resumen.append(("Eventos con user_id válido", usuarios_eventos_validos))
    resumen.append(("Eventos huérfanos (sin user_id en usuarios)", total_events - usuarios_eventos_validos))

    # --- 4. Consistencia temporal ---
    if {"event_timestamp", "created_at", "received_at"}.issubset(events.columns):
        eventos_desorden = (events["created_at"] < events["event_timestamp"]).sum()
        resumen.append(("Eventos con created_at < event_timestamp", int(eventos_desorden)))

        eventos_fuera_orden = (events["received_at"] < events["created_at"]).sum()
        resumen.append(("Eventos con received_at < created_at", int(eventos_fuera_orden)))

    # --- 5. Cobertura de dominios ---
    dominios = {}
    for col in ["country", "device", "subscription_type", "event_type"]:
        if col in users.columns or col in events.columns:
            df = users if col in users.columns else events
            dominios[col] = df[col].dropna().nunique()

    # --- 6. Crear resumen Markdown ---
    lines = []
    lines.append(f"# Auditoría de Calidad de Datos — {datetime.now():%Y-%m-%d %H:%M}")
    lines.append("\n## Resultados cuantitativos\n")
    lines.append("| Métrica | Valor |")
    lines.append("|----------|--------|")
    for m, v in resumen:
        lines.append(f"| {m} | {v:,} |")

    lines.append("\n## Diversidad de valores (cardinalidad)\n")
    lines.append("| Columna | Número de valores únicos |")
    lines.append("|----------|---------------------------|")
    for k, v in dominios.items():
        lines.append(f"| {k} | {v} |")

    # --- 7. Guardar informe ---
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Informe generado: {out_md}")

def main():
    auditoria_calidad(
        users_csv="data/cleaned/users_clean.csv",
        events_csv="data/cleaned/events_clean.csv",
        out_md="docs/QA_phase1.md"
    )

if __name__ == "__main__":
    main()
