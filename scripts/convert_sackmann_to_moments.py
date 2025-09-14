#!/usr/bin/env python3
"""
Convert Jeff Sackmann ATP matches CSVs into Sports Moment Retrieval Engine format.

This script works even if you only have the *matches* files (e.g. atp_matches_2012.csv).
For each match, it emits at least one "moment": the match point (synthetic commentary).
If the score suggests tiebreaks (e.g., "7-6"), we add a "tie-break" tag.

INPUT (one or more CSVs via --matches_glob):
  Expected columns (typical in Jeff Sackmann datasets):
    - tourney_name, surface, tourney_date (YYYYMMDD), round
    - winner_name, loser_name
    - score  (e.g., '6-4 7-6(5) 5-7 6-3')
    - (optional) tourney_level, tourney_id, match_num, best_of

OUTPUT:
  moments CSV with columns:
    id,sport,tournament,year,event,round,set,game,point,player1,player2,surface,source_url,commentary,summary,tags

USAGE:
  python scripts/convert_sackmann_to_moments.py \
    --matches_glob "data/external/atp/*.csv" \
    --out "data/raw/tennis_matches_moments.csv"

  (You can pass a glob covering multiple years, e.g. "data/external/atp_matches_20*.csv")

Then process + index:
  python scripts/prepare_data.py --input data/raw/tennis_matches_moments.csv --output data/processed/moments.csv
  python -m smre.cli index-local --data data/processed/moments.csv --index-dir data/index
"""
import argparse
import glob
import os
import re
import sys
from datetime import datetime
from typing import Optional

import pandas as pd

REQUIRED_OUTPUT_COLS = [
    "id","sport","tournament","year","event","round","set","game","point",
    "player1","player2","surface","source_url","commentary","summary","tags"
]

ROUND_NORMALIZE = {
    "R128": "Round of 128",
    "R64": "Round of 64",
    "R32": "Round of 32",
    "R16": "Round of 16",
    "QF": "Quarter-final",
    "SF": "Semi-final",
    "F":  "Final",
}

EXPECTED_INPUT_COLS = [
    "tourney_name","surface","tourney_date","round","winner_name","loser_name","score"
]

def parse_year(date_val) -> Optional[int]:
    """
    date_val may be int (YYYYMMDD), string, or NaN. Return 4-digit year or None.
    """
    if pd.isna(date_val):
        return None
    s = str(date_val)
    m = re.match(r"^\s*(\d{4})", s)
    return int(m.group(1)) if m else None

def has_tiebreak(score: str) -> bool:
    if not isinstance(score, str):
        return False
    s = score.upper()
    return "7-6" in s or "TB" in s or "(" in s  # rough heuristic

def round_human(round_raw: object) -> str:
    """
    Robust conversion of raw 'round' to a human label.
    Handles NaN/float/mixed types safely.
    """
    if pd.isna(round_raw):
        r = ""
    else:
        r = str(round_raw)
    r = r.strip().upper()  # now safe

    # Known short codes
    if r in ROUND_NORMALIZE:
        return ROUND_NORMALIZE[r]

    # Qualifying rounds like Q1, Q2...
    if r.startswith("Q") and r[1:].isdigit():
        return f"Qualifying {r[1:]}"

    # Common long-form strings (keep as-is but normalized casing if present)
    if r:
        # return a friendlier casing for unknown values
        return r.title()

    return "Unknown"

def championship_tag(round_name: str) -> str:
    return "championship point" if (round_name or "").lower() == "final" else ""

def safe_str(x: object) -> str:
    return "" if pd.isna(x) else str(x)

def build_commentary(row: pd.Series, round_name_human: str) -> str:
    tname = row.get("tourney_name") or row.get("tournament") or "Unknown Tournament"
    yr = parse_year(row.get("tourney_date"))
    w = row.get("winner_name") or "Unknown Winner"
    l = row.get("loser_name") or "Unknown Loser"
    score = row.get("score") or ""
    if (round_name_human or "").lower() == "final":
        return f"{w} strikes the final winning point to capture the {tname} {yr} title over {l}, closing it {score}."
    else:
        return f"{w} converts match point against {l} at {tname} {yr}, final score {score}."

def build_summary(row: pd.Series, round_name_human: str) -> str:
    tname = row.get("tourney_name") or "Tournament"
    yr = parse_year(row.get("tourney_date"))
    w = row.get("winner_name") or "Winner"
    l = row.get("loser_name") or "Loser"
    if (round_name_human or "").lower() == "final":
        return f"{w} wins {tname} {yr} Final vs {l}."
    else:
        return f"{w} defeats {l} at {tname} {yr}."

def normalize_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure expected columns exist and are string-typed (filled with "") to avoid mixed-type warnings.
    """
    # Add any missing expected columns first
    for col in EXPECTED_INPUT_COLS:
        if col not in df.columns:
            df[col] = pd.NA

    # Convert to pandas' nullable string dtype, then fill NaNs with ""
    for col in EXPECTED_INPUT_COLS:
        df[col] = df[col].astype("string")

    df[EXPECTED_INPUT_COLS] = df[EXPECTED_INPUT_COLS].fillna("")
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches_glob", required=True, help="Glob for atp_matches_*.csv files")
    ap.add_argument("--out", required=True, help="Output CSV path (moments format)")
    ap.add_argument("--event_name", default="Men's Singles", help="Default event name")
    ap.add_argument("--sport", default="tennis", help="Sport label")
    ap.add_argument("--source_url_prefix", default="", help="Optional URL prefix to link to your source")
    args = ap.parse_args()

    files = sorted(glob.glob(args.matches_glob))
    if not files:
        print(f"No files matched: {args.matches_glob}", file=sys.stderr)
        sys.exit(2)

    frames = []
    for f in files:
        try:
            # low_memory=False avoids mixed-type chunk inference warnings
            df = pd.read_csv(f, low_memory=False)
            df["__source_file__"] = f
            df = normalize_input_dataframe(df)
            frames.append(df)
        except Exception as e:
            print(f"Warning: failed to read {f}: {e}", file=sys.stderr)

    if not frames:
        print("No readable CSVs.", file=sys.stderr)
        sys.exit(2)

    mdf = pd.concat(frames, ignore_index=True)

    out_rows = []
    for i, row in mdf.iterrows():
        tname = safe_str(row["tourney_name"])
        yr = parse_year(row["tourney_date"])
        surface = safe_str(row["surface"])
        rnd_h = round_human(row["round"])
        p1 = safe_str(row["winner_name"])
        p2 = safe_str(row["loser_name"])
        score = safe_str(row["score"])

        # Deterministic-ish id
        mid = f"m_{yr if yr is not None else 'NA'}_" \
              f"{re.sub(r'[^A-Za-z0-9]+','',p1)[:10]}_" \
              f"{re.sub(r'[^A-Za-z0-9]+','',p2)[:10]}_{i}"

        # Tags
        tags = []
        if rnd_h.lower() == "final":
            tags.append("championship point")
        if has_tiebreak(score):
            tags.append("tie-break")
        if "RET" in score.upper():
            tags.append("retirement")
        tags.append("match point")

        # Commentary + summary
        commentary = build_commentary(row, rnd_h)
        summary = build_summary(row, rnd_h)

        out_rows.append({
            "id": mid,
            "sport": args.sport,
            "tournament": tname,
            "year": yr if yr is not None else "",
            "event": args.event_name,
            "round": rnd_h,
            "set": "",
            "game": "",
            "point": "Match Point",
            "player1": p1,
            "player2": p2,
            "surface": surface,
            "source_url": args.source_url_prefix,
            "commentary": commentary,
            "summary": summary,
            "tags": ";".join(tags)
        })

    out_df = pd.DataFrame(out_rows, columns=REQUIRED_OUTPUT_COLS)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {len(out_df)} moments to {args.out}")

if __name__ == "__main__":
    main()
