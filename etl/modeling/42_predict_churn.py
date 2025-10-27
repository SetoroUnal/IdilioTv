#!/usr/bin/env python3
import os
import argparse
import json
import joblib
import pandas as pd
from datetime import datetime

def load_artifact(model_path: str):
    artifact = joblib.load(model_path)
    if not isinstance(artifact, dict) or "model" not in artifact or "features" not in artifact:
        raise ValueError("El archivo .pkl no contiene el artefacto esperado {'model','features', 'threshold'}")
    model = artifact["model"]
    features = artifact["features"]
    threshold = artifact.get("threshold", 0.5)
    return model, features, threshold

def align_features(df: pd.DataFrame, features: list) -> pd.DataFrame:
    # Añade columnas faltantes como 0 y reordena
    for col in features:
        if col not in df.columns:
            df[col] = 0
    X = df[features].copy()
    # Descarta cualquier columna extra (no usada por el modelo)
    return X

def predict(
    model_pkl: str,
    input_csv: str,
    id_col: str,
    output_csv: str,
    topn: int = 0
):
    print(f"Cargando modelo: {model_pkl}")
    model, feature_names, threshold = load_artifact(model_pkl)
    print(f"Umbral aprendido: {threshold:.4f}")
    print(f"Total de features esperadas por el modelo: {len(feature_names)}")

    print(f"Cargando datos: {input_csv}")
    df = pd.read_csv(input_csv)

    if id_col not in df.columns:
        raise ValueError(f"No se encontró la columna de id '{id_col}' en {input_csv}")

    # Si viene con label, no lo uses para predecir
    for col in ["churn_30d", "events_D7", "events_D30"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    # Alinear columnas con entrenamiento
    X = align_features(df, feature_names)

    # Predicción
    print("Calculando probabilidades...")
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= threshold).astype(int)

    out = pd.DataFrame({
        id_col: df[id_col],
        "proba_churn": proba,
        "pred_churn": pred
    })
    out["threshold_used"] = threshold
    out["model_file"] = os.path.basename(model_pkl)
    out["scored_at_utc"] = datetime.utcnow().isoformat(timespec="seconds")

    # Guardar resultado
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    out.to_csv(output_csv, index=False)
    print(f"Predicciones guardadas en: {output_csv}")
    print(out.head(5).to_string(index=False))

    # Export opcional top-N por probabilidad de churn
    if topn and topn > 0:
        top_path = output_csv.replace(".csv", f"_top{topn}.csv")
        out.sort_values("proba_churn", ascending=False).head(topn).to_csv(top_path, index=False)
        print(f"TOP-{topn} usuarios con mayor riesgo guardado en: {top_path}")

def main():
    parser = argparse.ArgumentParser(description="Scoring de churn usando modelo entrenado")
    parser.add_argument("--model", required=True, help="Ruta al .pkl (logreg o rf)")
    parser.add_argument("--input", required=True, help="CSV con user_id y features (ej: data/features/model_data.csv)")
    parser.add_argument("--id-col", default="user_id", help="Nombre de la columna id (default: user_id)")
    parser.add_argument("--output", default="data/models/predictions.csv", help="CSV de salida con scoring")
    parser.add_argument("--topn", type=int, default=0, help="Exportar TOP-N por probabilidad de churn (opcional)")
    args = parser.parse_args()

    predict(
        model_pkl=args.model,
        input_csv=args.input,
        id_col=args.id_col,
        output_csv=args.output,
        topn=args.topn
    )

if __name__ == "__main__":
    main()
