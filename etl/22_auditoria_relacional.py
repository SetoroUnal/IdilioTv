#!/usr/bin/env python3
import pandas as pd
import os

def auditoria_relacional(users_csv, events_csv, out_md):
    users = pd.read_csv(users_csv)
    events = pd.read_csv(events_csv)

    total_users = len(users)
    total_events = len(events)

    # --- 1. Eventos con user_id válido ---
    valid_events = events[events["user_id"].isin(users["user_id"])]
    invalid_events = total_events - len(valid_events)

    # --- 2. Usuarios con al menos un evento ---
    active_users = valid_events["user_id"].nunique()
    inactive_users = total_users - active_users

    # --- 3. Distribución de eventos por usuario ---
    eventos_por_usuario = valid_events.groupby("user_id")["event_uuid"].count()
    eventos_por_usuario.describe().to_csv(out_md.replace(".md", "_dist.csv"))

    # --- 4. Reporte Markdown ---
    lines = []
    lines.append("# Auditoría Relacional — Idilio TV")
    lines.append(f"- Total de usuarios: {total_users:,}")
    lines.append(f"- Total de eventos: {total_events:,}")
    lines.append(f"- Eventos válidos (con user_id existente): {len(valid_events):,}")
    lines.append(f"- Eventos huérfanos (sin user_id en usuarios): {invalid_events:,}")
    lines.append(f"- Usuarios activos (con eventos): {active_users:,}")
    lines.append(f"- Usuarios sin eventos: {inactive_users:,}")

    lines.append("\n## Distribución de eventos por usuario (resumen)")
    lines.append("| Métrica | Valor |")
    lines.append("|----------|--------|")
    desc = eventos_por_usuario.describe().round(2)
    for k, v in desc.items():
        lines.append(f"| {k} | {v:,} |")

    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Informe generado: {out_md}")

def main():
    auditoria_relacional(
        users_csv="data/cleaned/users_clean.csv",
        events_csv="data/cleaned/events_clean.csv",
        out_md="docs/QA_relacional.md"
    )

if __name__ == "__main__":
    main()
