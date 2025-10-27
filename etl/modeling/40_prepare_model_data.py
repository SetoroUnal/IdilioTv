#!/usr/bin/env python3
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def prepare_model_data(features_csv, churn_csv, out_dir="data/features"):
    print("Cargando datasets...")

    # --- 1. Lectura ---
    features = pd.read_csv(features_csv)
    churn = pd.read_csv(churn_csv)

    print(f"Usuarios en features: {features.shape[0]:,}")
    print(f"Usuarios en churn:    {churn.shape[0]:,}")

    # --- 2. Validar integridad de llaves ---
    if features["user_id"].duplicated().any():
        raise ValueError("Duplicados en user_features.csv")
    if churn["user_id"].duplicated().any():
        raise ValueError("Duplicados en user_retention_metrics.csv")

    # --- 3. Merge ---
    merged = features.merge(
        churn[["user_id", "churn_30d"]],
        on="user_id",
        how="inner"
    )
    print(f"Usuarios tras merge:  {merged.shape[0]:,}")

    # --- 4. Validar ausencia de fuga temporal ---
    # (Recordatorio conceptual)
    # Asegúrate de que ninguna columna dependa de información posterior al día 30.
    if "last_active_date" in merged.columns:
        print("Eliminando 'last_active_date' para evitar fuga temporal")
        merged.drop(columns=["last_active_date"], inplace=True)

    # --- 5. Separar target ---
    y = merged["churn_30d"].astype(int)
    X = merged.drop(columns=["user_id", "churn_30d"])

    # --- 6. Detectar tipos de variables ---
    cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()

    print(f"Variables categóricas: {len(cat_cols)}")
    print(f"Variables numéricas:   {len(num_cols)}")

    # --- 7. One-Hot Encoding ---
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    # --- 8. Escalado ---
    scaler = StandardScaler()
    X[num_cols] = scaler.fit_transform(X[num_cols])

    # --- 9. Train/Test split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # --- 10. Guardar datasets ---
    os.makedirs(out_dir, exist_ok=True)
    X_train.to_csv(os.path.join(out_dir, "X_train.csv"), index=False)
    X_test.to_csv(os.path.join(out_dir, "X_test.csv"), index=False)
    y_train.to_csv(os.path.join(out_dir, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(out_dir, "y_test.csv"), index=False)
    merged.to_csv(os.path.join(out_dir, "model_data.csv"), index=False)

    print(f"   Datos analíticos guardados en {out_dir}")
    print(f"   X_train: {X_train.shape}, X_test: {X_test.shape}")
    print(f"   y_train: {y_train.shape}, y_test: {y_test.shape}")

    return X_train, X_test, y_train, y_test

def main():
    prepare_model_data(
        features_csv="data/features/user_features.csv",
        churn_csv="data/cohorts/user_retention_metrics.csv",
        out_dir="data/features"
    )

if __name__ == "__main__":
    main()
