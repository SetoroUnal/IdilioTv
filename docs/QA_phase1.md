# Auditoría de Calidad de Datos — 2025-10-26 11:58

## Resultados cuantitativos

| Métrica | Valor |
|----------|--------|
| Usuarios sin user_id | 0 |
| Eventos sin event_uuid | 0 |
| Eventos sin user_id | 0 |
| Duplicados user_id | 0 |
| Duplicados event_uuid | 0 |
| Eventos con user_id válido | 200,000 |
| Eventos huérfanos (sin user_id en usuarios) | 0 |
| Eventos con created_at < event_timestamp | 0 |
| Eventos con received_at < created_at | 0 |

## Diversidad de valores (cardinalidad)

| Columna | Número de valores únicos |
|----------|---------------------------|
| country | 8 |
| device | 2 |
| subscription_type | 3 |
| event_type | 7 |