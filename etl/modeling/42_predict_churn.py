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
        raise ValueError("El archivo .pkl no contiene el artefacto esperado {'model','features','threshold'}")
    model = artifact["model"]
    features = artifact["features"]
    threshold = artifact.get("threshold", 0.5)
    return model, features, threshold

def align_features(df: pd.DataFrame, features: list) -> pd.DataFrame:
    for col in features:
        if col not in df.columns:
            df[col] = 0
    X = df[features].copy()
    return X

def predict(model_pkl, input_csv, id_col, output_csv, topn=0):
    print(f"Cargando modelo: {model_pkl}")
    model, feature_names, threshold = load_artifact(model_pkl)
    print(f"Umbral aprendido: {threshold:.4f}")
    print(f"Total de features esperadas por el modelo: {len(feature_names)}")

    print(f"Cargando datos: {input_csv}")
    df = pd.read_csv(input_csv)

    if id_col not in df.columns:
        raise ValueError(f"No se encontró la columna '{id_col}' en {input_csv}")

    for col in ["churn_30d", "events_D7", "events_D30"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    X = align_features(df, feature_names)

    print("Calculando probabilidades...")
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= threshold).astype(int)

    out = pd.DataFrame({
        id_col: df[id_col],
        "proba_churn": proba,
        "pred_churn": pred,
        "threshold_used": threshold,
        "model_file": os.path.basename(model_pkl),
        "scored_at_utc": datetime.utcnow().isoformat(timespec="seconds")
    })

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    out.to_csv(output_csv, index=False)
    print(f"Predicciones guardadas en: {output_csv}")
    print(out.head(5).to_string(index=False))

    if topn and topn > 0:
        top_path = output_csv.replace(".csv", f"_top{topn}.csv")
        out.sort_values("proba_churn", ascending=False).head(topn).to_csv(top_path, index=False)
        print(f"TOP-{topn} usuarios con mayor riesgo guardado en: {top_path}")

def main():
    default_model = r"data\models\churn_model_logreg.pkl"
    default_input = r"data\features\model_data.csv"
    default_output = r"data\models\predictions_full.csv"

    parser = argparse.ArgumentParser(description="Scoring de churn usando modelo entrenado")
    parser.add_argument("--model", default=default_model, help="Ruta al .pkl del modelo")
    parser.add_argument("--input", default=default_input, help="CSV con user_id y features")
    parser.add_argument("--id-col", default="user_id", help="Columna de id (default: user_id)")
    parser.add_argument("--output", default=default_output, help="CSV de salida con scoring")
    parser.add_argument("--topn", type=int, default=50, help="Exportar TOP-N por probabilidad de churn (opcional)")
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
