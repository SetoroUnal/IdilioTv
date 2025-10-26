## Resultados de la Feature Store (30_generate_features.py)

**Archivo generado:** `data/features/user_features.csv`

**Columnas clave:**
- `event_count`: cantidad total de eventos por usuario.
- `recency_days`: días desde el último evento hasta la fecha máxima registrada.
- `unique_event_types`: número de tipos distintos de eventos.

**Validación:**
- Sin valores nulos en métricas agregadas.
- Recency calculada correctamente.
- Total de filas = total de usuarios (5,000).

## Visualización y validación

**Notebook:** `notebooks/02_retention_analysis.ipynb`

**Salidas:**
- Heatmap de retención mensual (`seaborn`)
- Curvas globales D7 / D30 / Churn
- Archivo de resumen: `docs/QA_retention_summary.csv`

**Conclusiones esperadas:**
- Descenso progresivo mes a mes (patrón normal de retención).
- Relación inversa entre recencia y churn.
- Tasa de retención D30 > 50 % indica buena retención de usuarios.

