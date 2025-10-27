#!/usr/bin/env python3
import argparse, os
import pandas as pd
from dateutil import parser as dtparser
import json

def to_datetime(s, utc=True):
    try:
        return pd.to_datetime(s, utc=utc, errors="coerce", infer_datetime_format=True)
    except Exception:
        return pd.to_datetime(s, utc=utc, errors="coerce")

def validate_users(df):
    issues = {}
    required = ["user_id","signup_date","last_active_date"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues["missing_columns"] = missing
        return df, issues

    ## eliminar target nativo para evitar fuga de información
    if "churned_30d" in df.columns:
        print("Eliminando columna 'churned_30d' del dataset original...")
        df = df.drop(columns=["churned_30d"])
    
    # Convertir fechas
    df["signup_date"] = to_datetime(df["signup_date"]).dt.normalize()
    df["last_active_date"] = to_datetime(df["last_active_date"]).dt.normalize()

    # Revisar nulos
    issues["null_user_id"] = int(df["user_id"].isna().sum())
    issues["null_signup_date"] = int(df["signup_date"].isna().sum())
    issues["null_last_active_date"] = int(df["last_active_date"].isna().sum())

    # Corregir inconsistencias temporales
    inconsistent = df["signup_date"] > df["last_active_date"]
    issues["temporal_inconsistencies"] = int(inconsistent.sum())
    if inconsistent.any():
        df.loc[inconsistent, ["signup_date","last_active_date"]] = df.loc[inconsistent, ["last_active_date","signup_date"]].values
        
    # Eliminar usuarios sin ID
    before = len(df)
    df = df[~df["user_id"].isna()].copy()
    issues["dropped_missing_user_id"] = int(before - len(df))

    # Deduplicar
    df.sort_values(by=["user_id","last_active_date"], ascending=[True, False], inplace=True)
    deduped = df.drop_duplicates(subset=["user_id"], keep="first")
    issues["duplicates_removed"] = int(len(df) - len(deduped))

    return deduped.reset_index(drop=True), issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.in_csv)
    cleaned, issues = validate_users(df)
    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    cleaned.to_csv(args.out_csv, index=False)

    qa_path = args.out_csv.replace(".csv",".qa.json")
    with open(qa_path, "w") as f:
        json.dump(issues, f, indent=2, default=str)

    print(f"Guardado: {args.out_csv}")
    print(f"Reporte QA: {qa_path}")

if __name__ == "__main__":
    main()
