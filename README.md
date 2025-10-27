# Head of Data & AI – Caso Técnico Idilio TV

## 1. Introducción

Este proyecto constituye la resolución integral del caso técnico **Head of Data & AI – Idilio TV**, un desafío diseñado para evaluar competencias de ingeniería y ciencia de datos aplicadas a la analítica de usuarios, segmentación y predicción de churn dentro de una plataforma de streaming.  

El objetivo fue construir un pipeline reproducible, auditable y analíticamente sólido que permita transformar datos crudos en información estratégica sobre el comportamiento de los usuarios, su retención y riesgo de abandono.

---

## 2. Contexto y objetivos del caso

**Objetivo general:** convertir los datos de usuarios y eventos en insights accionables sobre comportamiento, retención y churn, con enfoque en trazabilidad y calidad de datos.

**Preguntas guía:**
1. ¿Cómo se comportan los usuarios dentro de la aplicación?
2. ¿Qué patrones de uso y consumo existen por país, dispositivo o suscripción?
3. ¿Qué segmentos de usuarios se pueden identificar?
4. ¿Qué factores predicen la probabilidad de churn?
5. ¿Qué acciones de negocio pueden derivarse de los hallazgos?

**Datasets utilizados:**
- `idilio_user_data.csv` → información demográfica, suscripción, engagement.
- `idilio_analytics_events.csv` → eventos in-app: apertura, reproducción, pausa, siguiente episodio, etc.

---

## 3. Estructura del proyecto

```
IdilioTv/
├── data/
│   ├── raw/                      # Datos originales
│   ├── cleaned/                  # Datos limpios y validados (Fase 0)
│   ├── features/                 # Features derivadas (Fase 2)
│   ├── cohorts/                  # Cohortes y métricas de retención (Fase 3)
│   ├── models/                   # Modelos entrenados y predicciones (Fase 4)
│   └── analytics/                # Resultados intermedios
│
├── etl/
│   ├── 01_clean_users.py         # Limpieza de usuarios
│   ├── 02_clean_events.py        # Limpieza de eventos
│   ├── 21_auditoria_temporal.py  # Auditoría de consistencia temporal
│   ├── cohorts/31_cohorts_retention.py  # Cálculo de cohortes de retención
│   ├── features/30_generate_features.py # Feature engineering a nivel usuario
│   ├── modeling/41_train_churn_model.py # Entrenamiento de modelos
│   ├── modeling/42_predict_churn.py     # Scoring de usuarios
│   └── analysis/43_churn_scoring_QA.py  # QA y segmentación de riesgo
│
├── docs/                         # Reportes y visualizaciones
│   ├── QA_phase0.json
│   ├── retention_plots.png
│   ├── churn_segmented.csv
│   └── model_eval_summary.json
│
└── README.md
```



---

## 4. Desarrollo por fases

### Fase 0 – Limpieza y validación de datos

Se implementaron scripts independientes para `users` y `events`, con contratos de datos explícitos.  
Las validaciones incluyeron:
- Tipos de datos correctos (datetime, categorical, numeric)
- Verificación de llaves primarias (`user_id`, `event_uuid`)
- Ausencia de duplicados
- Consistencia temporal (`signup_date ≤ last_active_date ≤ event_timestamp`)

**Resultados QA:**
- Sin valores nulos en columnas clave.
- 0 duplicados.
- 133.206 inconsistencias detectadas en `created_at < received_at`, corregidas en la siguiente fase.

**Conclusión:** Datos listos para modelado y auditoría temporal.

---

### Fase 1 – Auditoría temporal

Objetivo: detectar desalineaciones entre los tiempos de creación y recepción de eventos.

**Métricas derivadas:**
- `delay_event_created` = `created_at - event_timestamp`
- `delay_created_received` = `received_at - created_at`

**Hallazgo:** los eventos tienen latencia controlada (~1s promedio) pero inconsistencias en orden de creación, indicativo de buffering o colas asíncronas en backend.

**Conclusión:** la fuente es confiable para análisis agregado, pero requiere cuidado al usar timestamps individuales para secuencias.

---

### Fase 2 – Feature Engineering

Se consolidaron atributos a nivel usuario con base en los eventos limpios.

**Features generadas:**
- `event_count` → número total de eventos.
- `recency_days` → días desde el último evento hasta la fecha máxima global.
- `unique_event_types` → número de tipos de eventos distintos por usuario.

**Dataset resultante:** `data/features/user_features.csv`

**Columnas finales:**  
Demografía + engagement + variables derivadas, totalizando 28 columnas.

---

### Fase 3 – Cohortes y retención

Cohortes mensuales basadas en `signup_date`, midiendo retención según actividad (`event_timestamp`).

**Variables:**
- `cohort_month`, `event_month`, `retention_rate`.
- Métricas D7, D30 y churn_30d calculadas por usuario.

**Resultados:**
- Tasa de retención D7 = 9.6 %
- Tasa de retención D30 = 15.2 %
- Churn 30d = 84.8 %

**Conclusión:** se valida fuerte desbalance (≈85 % churners).  
La métrica original `churned_30d` del dataset fue reemplazada por una versión recalculada para garantizar consistencia temporal.

---

### Fase 4 – Modelado predictivo y scoring

Dos modelos se entrenaron sobre 5.000 usuarios:
- `LogisticRegression(class_weight='balanced')`
- `RandomForestClassifier(class_weight='balanced')`

**Resultados:**
| Modelo | AUC | Recall | Precision | F1 | Threshold |
|---------|-----|---------|------------|----|-----------|
| Logistic Regression | 0.964 | 1.000 | 0.848 | 0.918 | 0.071 |
| Random Forest | 0.755 | 1.000 | 0.848 | 0.918 | 0.362 |

**Interpretación:** excelente capacidad de discriminación, pero alta sobreconfianza (predicciones saturadas cerca de 1.0).  
Se priorizó *recall* por sobre precisión, siguiendo criterio de negocio: **mejor detectar churners que omitirlos.**

**Archivos generados:**
- `data/models/churn_model_logreg.pkl`
- `data/models/churn_model_rf.pkl`
- `docs/model_eval_summary.json`

---

### Fase 4.2 – Scoring y segmentación de riesgo

El modelo logístico se utilizó para generar `proba_churn` para cada usuario.  
Dado el sesgo de calibración, se establecieron **segmentos relativos** por percentiles:

| Segmento | % usuarios | Descripción |
|-----------|-------------|--------------|
| High Risk | 20.7 % | Top 20 % con mayor probabilidad de churn |
| Medium Risk | 39.3 % | Riesgo medio (40–80 %) |
| Low Risk | 40.0 % | Menor riesgo |

**Distribución promedio por país:** Perú, Chile y Venezuela presentan mayor riesgo.  
**Por dispositivo:** iOS > Android.  
**Por suscripción:** basic > premium.

**Conclusión:** el modelo sirve como herramienta de ranking y segmentación interna, no como estimador de probabilidad calibrada.  
Próximo paso sugerido: calibración vía `CalibratedClassifierCV` o `Platt Scaling`.

---

## 5. Informe ejecutivo

### Contexto
Idilio TV busca escalar su base de usuarios maximizando retención y monetización. El análisis identifica patrones críticos de uso y riesgo de abandono, proporcionando una base para acciones de retención y campañas personalizadas.

### Hallazgos clave
1. Alta concentración de churn (≈85 %): requiere revisión de experiencia inicial y contenido recomendado.
2. Retención temprana baja (D7 < 10 %): la primera semana es decisiva; sugiere necesidad de onboarding o comunicación dirigida.
3. Segmentos con riesgo alto: usuarios *basic* en países pequeños (Perú, Chile, Venezuela) con comportamiento móvil iOS.
4. El modelo discrimina bien (AUC 0.96), pero necesita calibración para uso operativo.
5. Top 20 % High-Risk es priorizable para campañas de retención o cross-selling.

### Recomendaciones
- Implementar campañas automáticas para High-Risk con mensajes o promociones personalizadas.
- Introducir programas de lealtad para convertir Medium-Risk en usuarios retenidos.
- Ajustar UX inicial y secuencias de contenido para reforzar hábito en los primeros 7 días.
- Explorar modelos de recomendación para mejorar engagement.

---

## 6. Próximos pasos

| Fase | Descripción | Objetivo |
|-------|--------------|-----------|
| 5 | Segmentación no supervisada (KMeans o GMM) | Identificar clusters de usuarios por comportamiento |
| 6 | Calibración y modelado avanzado (XGBoost, SHAP) | Mejorar precisión e interpretabilidad |
| 7 | Dashboard en Power BI / Looker Studio | Monitoreo continuo de KPIs de retención |

---

## 7. Apéndice técnico

### Variables clave
- `churn_30d`: 1 si el usuario no tuvo actividad en los 30 días posteriores al registro.
- `recency_days`: días desde el último evento registrado.
- `unique_event_types`: diversidad de interacción dentro del app.
- `cohort_month`: mes de alta del usuario.

### Decisiones de diseño
- `churned_30d` original fue descartada por inconsistencias y recalculada.
- Se priorizó recall en los modelos, por el costo de falso negativo.
- Las probabilidades de churn se interpretan como ranking, no como tasas absolutas.

### Limitaciones conocidas
- Dataset sintético, no representa ruido real de un entorno de producción.
- Latencia artificial entre `created_at` y `received_at`.

---

## 8. Créditos

**Autor:** Proyecto desarrollado para la prueba técnica *Head of Data & AI – Idilio TV*.

**Repositorio:** [https://github.com/SetoroUnal/IdilioTv](https://github.com/SetoroUnal/IdilioTv)

**Fecha de última actualización:** Octubre 2025.
