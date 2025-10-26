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

def validate_events(df):
    issues = {}
    required = ["event_uuid","user_id","event_type","event_timestamp"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues["missing_columns"] = missing
        return df, issues

    for c in ["event_timestamp","received_at","created_at"]:
        if c in df.columns:
            df[c] = to_datetime(df[c])

    issues["null_event_uuid"] = int(df["event_uuid"].isna().sum())
    issues["null_user_id"] = int(df["user_id"].isna().sum())
    issues["null_event_timestamp"] = int(df["event_timestamp"].isna().sum())

    before = len(df)
    df = df[~df["event_uuid"].isna()].copy()
    df.sort_values(by=["event_uuid","event_timestamp"], inplace=True)
    deduped = df.drop_duplicates(subset=["event_uuid"], keep="first")
    issues["duplicates_removed"] = int(before - len(deduped))

    if "received_at" in deduped.columns:
        issues["received_before_event"] = int((deduped["received_at"] < deduped["event_timestamp"]).sum())
    if "created_at" in deduped.columns and "received_at" in deduped.columns:
        issues["created_before_received"] = int((deduped["created_at"] > deduped["received_at"]).sum())

    return deduped.reset_index(drop=True), issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.in_csv)
    cleaned, issues = validate_events(df)
    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    cleaned.to_csv(args.out_csv, index=False)

    qa_path = args.out_csv.replace(".csv",".qa.json")
    with open(qa_path, "w") as f:
        json.dump(issues, f, indent=2, default=str)

    print(f"Guardado: {args.out_csv}")
    print(f"Reporte QA: {qa_path}")

if __name__ == "__main__":
    main()
