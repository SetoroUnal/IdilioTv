#!/usr/bin/env python3
import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, roc_curve, precision_recall_curve,
    classification_report, confusion_matrix
)

# =========================================
# Utilidades SIN GRÁFICOS (solo CSV/JSON)
# =========================================
def evaluate_at_threshold(y_true, y_proba, thresh):
    y_pred = (y_proba >= thresh).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0,1])
    report = classification_report(y_true, y_pred, digits=4, output_dict=True)
    auc = roc_auc_score(y_true, y_proba)
    return {
        "threshold": float(thresh),
        "auc": float(auc),
        "confusion_matrix": {
            "tn": int(cm[0,0]), "fp": int(cm[0,1]),
            "fn": int(cm[1,0]), "tp": int(cm[1,1])
        },
        "precision_pos": float(report["1"]["precision"]),
        "recall_pos": float(report["1"]["recall"]),
        "f1_pos": float(report["1"]["f1-score"]),
        "support_pos": int(report["1"]["support"]),
        "precision_neg": float(report["0"]["precision"]),
        "recall_neg": float(report["0"]["recall"]),
        "f1_neg": float(report["0"]["f1-score"]),
        "support_neg": int(report["0"]["support"])
    }

def pick_threshold_by_recall(y_true, y_proba, min_recall=0.60, min_precision=0.15):
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    # thresholds tiene len = len(precisions)-1
    for i, thr in enumerate(thresholds):
        p, r = precisions[i], recalls[i]
        if r >= min_recall and p >= min_precision:
            return float(thr)
    # fallback: maximizar F1
    f1s = []
    for i, thr in enumerate(thresholds):
        p, r = precisions[i], recalls[i]
        f1s.append(0.0 if (p+r)==0 else 2*p*r/(p+r))
    best_idx = int(np.argmax(f1s))
    return float(thresholds[best_idx])

def dump_curves_to_csv(y_true, y_proba, model_name, out_docs_dir):
    os.makedirs(out_docs_dir, exist_ok=True)

    # ROC
    fpr, tpr, thr_roc = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)

    # Empatar longitudes de forma robusta
    min_len = min(len(fpr), len(tpr), len(thr_roc))
    roc_df = pd.DataFrame({
        "fpr": fpr[:min_len],
        "tpr": tpr[:min_len],
        "threshold": thr_roc[:min_len]
    })
    roc_path = os.path.join(out_docs_dir, f"roc_points_{model_name}.csv")
    roc_df.to_csv(roc_path, index=False)

    # PR
    precisions, recalls, thr_pr = precision_recall_curve(y_true, y_proba)
    pr_len = min(len(precisions), len(recalls))
    pr_df = pd.DataFrame({
        "recall": recalls[:pr_len],
        "precision": precisions[:pr_len]
    })
    pr_path = os.path.join(out_docs_dir, f"pr_points_{model_name}.csv")
    pr_df.to_csv(pr_path, index=False)

    return {"roc_csv": roc_path, "pr_csv": pr_path, "auc": float(auc)}


def sweep_thresholds(y_true, y_proba, steps=50):
    # barrido uniforme entre 0 y 1 excluyendo extremos que dan todo 0/1
    grid = np.linspace(0.01, 0.99, steps)
    rows = []
    for t in grid:
        m = evaluate_at_threshold(y_true, y_proba, t)
        rows.append({
            "threshold": m["threshold"],
            "auc": m["auc"],
            "precision_pos": m["precision_pos"],
            "recall_pos": m["recall_pos"],
            "f1_pos": m["f1_pos"],
            "tn": m["confusion_matrix"]["tn"],
            "fp": m["confusion_matrix"]["fp"],
            "fn": m["confusion_matrix"]["fn"],
            "tp": m["confusion_matrix"]["tp"],
        })
    return pd.DataFrame(rows)

# =========================================
# Entrenamiento principal
# =========================================
def train_and_eval_models(
    x_train_csv=r"C:\Users\Setoro\Desktop\Idilio\IdilioTv\data\features\X_train.csv",
    x_test_csv =r"C:\Users\Setoro\Desktop\Idilio\IdilioTv\data\features\X_test.csv",
    y_train_csv=r"C:\Users\Setoro\Desktop\Idilio\IdilioTv\data\features\y_train.csv",
    y_test_csv =r"C:\Users\Setoro\Desktop\Idilio\IdilioTv\data\features\y_test.csv",
    out_models_dir=r"C:\Users\Setoro\Desktop\Idilio\IdilioTv\data\models",
    out_docs_dir  =r"C:\Users\Setoro\Desktop\Idilio\IdilioTv\docs"
):
    print("Cargando datasets de entrenamiento/prueba...")
    X_train = pd.read_csv(x_train_csv)
    X_test  = pd.read_csv(x_test_csv)
    y_train = pd.read_csv(y_train_csv).iloc[:,0].astype(int)
    y_test  = pd.read_csv(y_test_csv).iloc[:,0].astype(int)

    print(f"X_train: {X_train.shape} | X_test: {X_test.shape}")
    print(f"y_train: {y_train.value_counts(normalize=True).round(3).to_dict()}")

    os.makedirs(out_models_dir, exist_ok=True)
    os.makedirs(out_docs_dir, exist_ok=True)

    results = {}

    # ------------------------
    # Modelo 1: Logistic Regression
    # ------------------------
    print("\nEntrenando LogisticRegression (class_weight='balanced')...")
    lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    lr.fit(X_train, y_train)
    proba_lr = lr.predict_proba(X_test)[:,1]

    # Umbral
    thr_lr = pick_threshold_by_recall(y_test, proba_lr, min_recall=0.60, min_precision=0.15)
    eval_lr = evaluate_at_threshold(y_test, proba_lr, thr_lr)

    # Curvas a CSV (no PNG)
    curves_lr = dump_curves_to_csv(y_test, proba_lr, "logreg", out_docs_dir)

    # Importancias (coeficientes)
    coef_df = pd.DataFrame({
        "feature": X_train.columns,
        "importance": lr.coef_[0]
    }).sort_values("importance", key=np.abs, ascending=False)
    coef_path = os.path.join(out_docs_dir, "feature_importance_logreg.csv")
    coef_df.to_csv(coef_path, index=False)

    # Guardar artefacto
    joblib.dump({"model": lr, "threshold": thr_lr, "features": list(X_train.columns)},
                os.path.join(out_models_dir, "churn_model_logreg.pkl"))

    # Sweeps
    sweep_lr = sweep_thresholds(y_test, proba_lr, steps=60)
    sweep_lr_path = os.path.join(out_docs_dir, "threshold_sweep_logreg.csv")
    sweep_lr.to_csv(sweep_lr_path, index=False)

    results["logreg"] = {
        "evaluation": eval_lr,
        "curves_csv": curves_lr,
        "importance_csv": coef_path,
        "sweep_csv": sweep_lr_path
    }

    # ------------------------
    # Modelo 2: Random Forest
    # ------------------------
    print("\nEntrenando RandomForestClassifier (class_weight='balanced')...")
    rf = RandomForestClassifier(
        n_estimators=400,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    proba_rf = rf.predict_proba(X_test)[:,1]

    thr_rf = pick_threshold_by_recall(y_test, proba_rf, min_recall=0.60, min_precision=0.15)
    eval_rf = evaluate_at_threshold(y_test, proba_rf, thr_rf)

    curves_rf = dump_curves_to_csv(y_test, proba_rf, "rf", out_docs_dir)

    # Importancias (Gini)
    imp_df = pd.DataFrame({
        "feature": X_train.columns,
        "importance": rf.feature_importances_
    }).sort_values("importance", ascending=False)
    imp_path = os.path.join(out_docs_dir, "feature_importance_rf.csv")
    imp_df.to_csv(imp_path, index=False)

    joblib.dump({"model": rf, "threshold": thr_rf, "features": list(X_train.columns)},
                os.path.join(out_models_dir, "churn_model_rf.pkl"))

    sweep_rf = sweep_thresholds(y_test, proba_rf, steps=60)
    sweep_rf_path = os.path.join(out_docs_dir, "threshold_sweep_rf.csv")
    sweep_rf.to_csv(sweep_rf_path, index=False)

    results["random_forest"] = {
        "evaluation": eval_rf,
        "curves_csv": curves_rf,
        "importance_csv": imp_path,
        "sweep_csv": sweep_rf_path
    }

    # ------------------------
    # Resumen comparativo (JSON)
    # ------------------------
    summary = {
        "logreg": {
            "AUC": results["logreg"]["curves_csv"]["auc"],
            "Recall": results["logreg"]["evaluation"]["recall_pos"],
            "Precision": results["logreg"]["evaluation"]["precision_pos"],
            "F1": results["logreg"]["evaluation"]["f1_pos"],
            "Threshold": results["logreg"]["evaluation"]["threshold"]
        },
        "random_forest": {
            "AUC": results["random_forest"]["curves_csv"]["auc"],
            "Recall": results["random_forest"]["evaluation"]["recall_pos"],
            "Precision": results["random_forest"]["evaluation"]["precision_pos"],
            "F1": results["random_forest"]["evaluation"]["f1_pos"],
            "Threshold": results["random_forest"]["evaluation"]["threshold"]
        }
    }

    with open(os.path.join(out_docs_dir, "model_eval_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n== Resumen (sin gráficos, con CSV de curvas) ==")
    for name, met in summary.items():
        print(f"{name:>12}: AUC={met['AUC']:.3f} | Recall={met['Recall']:.3f} | Precision={met['Precision']:.3f} | F1={met['F1']:.3f} | thr={met['Threshold']:.3f}")

    print(f"\nModelos guardados en: {out_models_dir}")
    print(f"Reportes/curvas CSV en: {out_docs_dir}")

def main():
    train_and_eval_models()

if __name__ == "__main__":
    main()
