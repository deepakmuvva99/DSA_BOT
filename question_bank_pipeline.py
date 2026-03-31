"""
Monthly question bank expansion pipeline.

Usage:
python question_bank_pipeline.py --tracker DSA_Master_Tracker.xlsx --import-file imports/new_questions.csv
"""

import argparse
import os
import sys

import pandas as pd


EXPECTED_COLUMNS = {
    "DSA Problems": [
        "Problem Name",
        "LeetCode Link",
        "Category",
        "Pattern",
        "Difficulty",
        "Status",
        "First Attempt Date",
        "Revision 1",
        "Revision 2",
        "Revision 3",
        "Time Taken (min)",
        "Accuracy (%)",
        "Confidence (1-5)",
        "Notes",
    ]
}


def _normalize_columns(df: pd.DataFrame, target_sheet: str) -> pd.DataFrame:
    expected = EXPECTED_COLUMNS[target_sheet]
    out = df.copy()

    for col in expected:
        if col not in out.columns:
            out[col] = ""

    # Default values for newly imported rows
    if "Status" in out.columns:
        out["Status"] = out["Status"].replace("", "Not Started").fillna("Not Started")
    if "Confidence (1-5)" in out.columns:
        out["Confidence (1-5)"] = pd.to_numeric(out["Confidence (1-5)"], errors="coerce").fillna(3)

    return out[expected]


def merge_dsa_questions(tracker_path: str, import_file: str):
    existing = pd.read_excel(tracker_path, sheet_name="DSA Problems")
    new_df = pd.read_csv(import_file)
    new_df = _normalize_columns(new_df, "DSA Problems")

    existing_links = set(existing["LeetCode Link"].astype(str).str.strip().str.lower())
    existing_names = set(existing["Problem Name"].astype(str).str.strip().str.lower())

    filtered = new_df[
        ~new_df["LeetCode Link"].astype(str).str.strip().str.lower().isin(existing_links)
        & ~new_df["Problem Name"].astype(str).str.strip().str.lower().isin(existing_names)
    ].copy()

    if len(filtered) == 0:
        print("No new unique DSA questions to import.")
        return

    merged = pd.concat([existing, filtered], ignore_index=True)
    with pd.ExcelWriter(
        tracker_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        merged.to_excel(writer, index=False, sheet_name="DSA Problems")

    print(f"Imported {len(filtered)} new DSA questions into tracker.")


def parse_args():
    parser = argparse.ArgumentParser(description="Monthly DSA question bank import pipeline")
    parser.add_argument("--tracker", required=True, help="Path to tracker xlsx file")
    parser.add_argument("--import-file", required=True, help="Path to CSV containing new DSA questions")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not os.path.exists(args.tracker):
        print(f"Tracker file not found: {args.tracker}")
        sys.exit(1)
    if not os.path.exists(args.import_file):
        print(f"Import file not found: {args.import_file}")
        sys.exit(1)

    merge_dsa_questions(args.tracker, args.import_file)
