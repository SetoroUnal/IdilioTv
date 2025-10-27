#!/usr/bin/env python3
import os
import json
import joblib
import numpy as np
import pandas as pd


from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, roc_curve,
    precision_recall_curve, classification_report,
    confusion_matrix
)

# ----------------------------
# Utilidades
# ----------------------------

def evaluate_at_threshold(y_true, y_proba, thresh):
    y_pred = (y_proba >= thresh).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0,1])
    report = classification_report(y_true, y_pred, digits=3, output_dict=True)
    auc = roc_auc_score(y_true, y_proba)
    return {
        "threshold": float(thresh),
        "auc": float(auc),
        "confusion_matrix": {
            "tn": int(cm[0,0]), "fp": int(cm[0,1]),
            "fn": int(cm[1,0]), "tp": int(cm[1,1])
        },
        "precision": float(report["1"]["precision"]),
        "recall": float(report["1"]["recall"]),
        "f1": float(report["1"]["f1-score"]),
        "support_pos": int(report["1"]["support"]),
        "support_neg": int(report["0"]["support"])
    }

def pick_threshold_by_recall(y_true, y_proba, min_recall=0.60, min_precision=0.15):
    """Elige el menor umbral que logra al menos min_recall y min_precision (clase positiva=churn=1).
       Si no hay ninguno, devuelve el que maximiza F1."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    # thresholds tiene len = len(precisions)-1
    best_idx = None
    for i in range(len(thresholds)):
        p = precisions[i]
        r = recalls[i]
        if r >= min_recall and p >= min_precision:
            best_idx = i
            break
    if best_idx is not None:
        return float(thresholds[best_idx])

    # fallback: maximizar F1
    f1s = []
    for i in range(len(thresholds)):
        p = precisions[i]
        r = recalls[i]
        if p + r > 0:
            f1s.append(2*p*r/(p+r))
        else:
            f1s.append(0.0)
    best_idx = int(np.argmax(f1s))
    return float(thresholds[best_idx])

def safe_plot_curves(y_true, y_proba, model_name, out_dir_docs):
    """Guarda ROC y PR si matplotlib está disponible; si no, continúa sin fallar."""
    try:
        print(f"[DEBUG] Intentando guardar gráficos en: {out_dir_docs}")
        print(f"[DEBUG] Tipo de out_dir_docs: {type(out_dir_docs)} - Existe: {os.path.exists(out_dir_docs)}")

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt


        fpr, tpr, _ = roc_curve(y_true, y_proba)
        auc = roc_auc_score(y_true, y_proba)

        os.makedirs(out_dir_docs, exist_ok=True)

        # ROC
        plt.figure()
        plt.plot(fpr, tpr, label=f"{model_name} (AUC={auc:.3f})")
        plt.plot([0,1], [0,1], linestyle="--")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"ROC - {model_name}")
        plt.legend(loc="lower right")
        roc_path = os.path.join(out_dir_docs, f"roc_{model_name}.png")
        print(f"[DEBUG] Guardando ROC en: {roc_path}")
        plt.savefig(roc_path, bbox_inches="tight")
        plt.close()

        # PR
        precisions, recalls, _ = precision_recall_curve(y_true, y_proba)
        plt.figure()
        plt.plot(recalls, precisions)
        plt.xlabel("Recall (Positive class: churn=1)")
        plt.ylabel("Precision")
        plt.title(f"Precision-Recall - {model_name}")
        pr_path = os.path.join(out_dir_docs, f"pr_{model_name}.png")
        print(f"[DEBUG] Guardando ROC en: {roc_path}")
        plt.savefig(pr_path, bbox_inches="tight")
        plt.close()

        return {"roc_path": roc_path, "pr_path": pr_path}
    except Exception as e:
        return {"warning": f"No se generaron gráficos (matplotlib no disponible o error): {e}"}

# ----------------------------
# Entrenamiento
# ----------------------------

def train_and_eval_models(
    x_train_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/X_train.csv",
    x_test_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/X_test.csv",
    y_train_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/y_train.csv",
    y_test_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/y_test.csv",
    out_models_dir="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/models",
    out_docs_dir="C:/Users/Setoro/Desktop/Idilio/IdilioTv/docs"
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
    lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42, n_jobs=None)
    lr.fit(X_train, y_train)
    proba_lr = lr.predict_proba(X_test)[:,1]

    # Selección de umbral (priorizamos recall con un mínimo de precision)
    thresh_lr = pick_threshold_by_recall(y_test, proba_lr, min_recall=0.60, min_precision=0.15)
    eval_lr = evaluate_at_threshold(y_test, proba_lr, thresh_lr)
    curves_lr = safe_plot_curves(y_test, proba_lr, "logreg", out_docs_dir)

    # Guardar artefacto
    lr_artifact = {
        "model_type": "LogisticRegression",
        "sk_params": lr.get_params(),
        "feature_names": list(X_train.columns),
        "threshold": eval_lr["threshold"]
    }
    joblib.dump({"model": lr, "threshold": eval_lr["threshold"], "features": list(X_train.columns)},
                os.path.join(out_models_dir, "churn_model_logreg.pkl"))

    results["logreg"] = {
        "evaluation": eval_lr,
        "plots": curves_lr,
        "artifact": lr_artifact
    }

    # ------------------------
    # Modelo 2: Random Forest (sin nuevas dependencias)
    # ------------------------
    print("\nEntrenando RandomForestClassifier (balanceado vía class_weight)...")
    rf = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    proba_rf = rf.predict_proba(X_test)[:,1]

    thresh_rf = pick_threshold_by_recall(y_test, proba_rf, min_recall=0.60, min_precision=0.15)
    eval_rf = evaluate_at_threshold(y_test, proba_rf, thresh_rf)
    curves_rf = safe_plot_curves(y_test, proba_rf, "rf", out_docs_dir)

    joblib.dump({"model": rf, "threshold": eval_rf["threshold"], "features": list(X_train.columns)},
                os.path.join(out_models_dir, "churn_model_rf.pkl"))

    results["random_forest"] = {
        "evaluation": eval_rf,
        "plots": curves_rf,
        "artifact": {
            "model_type": "RandomForestClassifier",
            "sk_params": rf.get_params(),
            "feature_names": list(X_train.columns),
            "threshold": eval_rf["threshold"]
        }
    }

    # ------------------------
    # Resumen comparativo
    # ------------------------
    summary = {
        "logreg": {
            "AUC": results["logreg"]["evaluation"]["auc"],
            "Recall": results["logreg"]["evaluation"]["recall"],
            "Precision": results["logreg"]["evaluation"]["precision"],
            "F1": results["logreg"]["evaluation"]["f1"],
            "Threshold": results["logreg"]["evaluation"]["threshold"]
        },
        "random_forest": {
            "AUC": results["random_forest"]["evaluation"]["auc"],
            "Recall": results["random_forest"]["evaluation"]["recall"],
            "Precision": results["random_forest"]["evaluation"]["precision"],
            "F1": results["random_forest"]["evaluation"]["f1"],
            "Threshold": results["random_forest"]["evaluation"]["threshold"]
        }
    }

    with open(os.path.join(out_docs_dir, "model_eval_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n== Resumen (umbral ajustado por recall mínimo) ==")
    for name, met in summary.items():
        print(f"{name:>12}: AUC={met['AUC']:.3f} | Recall={met['Recall']:.3f} | Precision={met['Precision']:.3f} | F1={met['F1']:.3f} | thr={met['Threshold']:.3f}")

    print(f"\nModelos guardados en: {out_models_dir}")
    print(f"Métricas/plots en: {out_docs_dir}")

def main():
    train_and_eval_models(
        x_train_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/X_train.csv",
        x_test_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/X_test.csv",
        y_train_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/y_train.csv",
        y_test_csv="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/features/y_test.csv",
        out_models_dir="C:/Users/Setoro/Desktop/Idilio/IdilioTv/data/models",
        out_docs_dir="C:/Users/Setoro/Desktop/Idilio/IdilioTv/docs"
    )

if __name__ == "__main__":
    main()
