# QA Phase 0 – Resultados de Limpieza Inicial

## Usuarios (`users_clean.qa.json`)

```json
{
  "null_user_id": 0,
  "null_signup_date": 0,
  "null_last_active_date": 0,
  "temporal_inconsistencies": 0,
  "dropped_missing_user_id": 0,
  "duplicates_removed": 0
}

```
## Conclusión:

-Sin valores nulos.

-Sin inconsistencias temporales.

-Sin duplicados.

-Cumple 100 % con el contrato de datos.

```json
{
  "null_event_uuid": 0,
  "null_user_id": 0,
  "null_event_timestamp": 0,
  "duplicates_removed": 0,
  "received_before_event": 0,
  "created_before_received": 133206
}
```

## Conclusión:

-Llaves completas y sin duplicados.

-Integridad entre usuario y evento: correcta.

-Inconsistencia detectada en created_at < received_at (133 206 registros, ~x % del total).
Requiere revisión en la fase 1.