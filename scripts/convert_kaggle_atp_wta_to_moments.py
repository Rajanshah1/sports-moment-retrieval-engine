#!/usr/bin/env python3
"""
Convert Kaggle ATP/WTA daily-update match CSVs to Sports-Moment-Retrieval-Engine moments.csv

Works with datasets like:
- dissfya/atp-tennis-2000-2023daily-pull
- dissfya/wta-tennis-2007-2023-daily-update

It expects match-level rows (one per match) with columns similar to Jeff Sackmann format.
For each match, we synthesize a single 'Match Point' moment with readable commentary.

USAGE (ATP):
  python scripts/convert_kaggle_atp_wta_to_moments.py     --matches_glob "data/external/atp/*.csv"     --sport tennis     --event "Men's Singles"     --out "data/raw/atp_matches_moments.csv"

USAGE (WTA):
  python scripts/convert_kaggle_atp_wta_to_moments.py     --matches_glob "data/external/wta/*.csv"     --sport tennis     --event "Women's Singles"     --out "data/raw/wta_matches_moments.csv"
"""
import argparse, glob, os, re, sys
import pandas as pd

REQUIRED_OUTPUT_COLS = [
    "id","sport","tournament","year","event","round","set","game","point",
    "player1","player2","surface","source_url","commentary","summary","tags"
]

ROUND_MAP = {"F":"Final","SF":"Semi-final","QF":"Quarter-final",
             "R16":"Round of 16","R32":"Round of 32","R64":"Round of 64","R128":"Round of 128"}

def pick(df, names):
    for n in names:
        if n in df.columns: return n
        for c in df.columns:
            if c.lower() == n.lower(): return c
    return None

def normalize_round(r):
    if r is None: return ""
    r = str(r).strip()
    return ROUND_MAP.get(r, r)

def parse_year(v):
    if pd.isna(v): return ""
    s = str(v)
    # Handles YYYY or YYYYMMDD
    if len(s) >= 4 and s[:4].isdigit():
        return s[:4]
    return ""

def clean(s): return re.sub(r"[^A-Za-z0-9]+","", str(s))[:12]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches_glob", required=True)
    ap.add_argument("--sport", default="tennis")
    ap.add_argument("--event", default="Men's Singles")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source_url_prefix", default="", help="Optional prefix if you have canonical links")
    args = ap.parse_args()

    files = sorted(glob.glob(args.matches_glob))
    if not files:
        print(f"No files matched: {args.matches_glob}", file=sys.stderr); sys.exit(2)

    out_rows = []
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"Skip {f}: {e}", file=sys.stderr); continue

        # Column detection across common Kaggle dumps
        c_tourney = pick(df, ["tourney_name","tournament","tourney","event_name"])
        c_surface = pick(df, ["surface"])
        c_date    = pick(df, ["tourney_date","date","match_date","start_date"])
        c_round   = pick(df, ["round"])
        c_winner  = pick(df, ["winner_name","winner","player1","p1"])
        c_loser   = pick(df, ["loser_name","loser","player2","p2"])
        c_score   = pick(df, ["score","final_score","match_score"])

        for i, r in df.iterrows():
            tname   = str(r.get(c_tourney, "")).strip()
            surface = str(r.get(c_surface, "")).strip()
            year    = parse_year(r.get(c_date, ""))
            rnd     = normalize_round(r.get(c_round, ""))
            p1      = str(r.get(c_winner, "")).strip()
            p2      = str(r.get(c_loser, "")).strip()
            score   = str(r.get(c_score, "")).strip()

            # Moment ID
            mid = f"kgl_{clean(year)}_{clean(tname)}_{clean(p1)}_{clean(p2)}_{i}"

            # Commentary / Summary
            if rnd and rnd.lower()=="final":
                commentary = f"{p1 or 'Winner'} secures the final point to win {tname} {year} against {p2 or 'opponent'}, closing {score or 'the match'}."
                summary    = f"{p1 or 'Winner'} wins {tname} {year} Final vs {p2 or 'opponent'}."
                tags = "championship point;match point"
            else:
                commentary = f"{p1 or 'Winner'} converts match point against {p2 or 'opponent'} at {tname or 'tournament'} {year}, final score {score or ''}."
                summary    = f"{p1 or 'Winner'} defeats {p2 or 'opponent'} at {tname or 'tournament'} {year}."
                tags = "match point"

            out_rows.append({
                "id": mid,
                "sport": args.sport,
                "tournament": tname,
                "year": year,
                "event": args.event,
                "round": rnd,
                "set": "",
                "game": "",
                "point": "Match Point",
                "player1": p1,
                "player2": p2,
                "surface": surface,
                "source_url": args.source_url_prefix,
                "commentary": commentary,
                "summary": summary,
                "tags": tags
            })

    if not out_rows:
        print("No rows created. Check your input files/columns.", file=sys.stderr); sys.exit(2)

    out = pd.DataFrame(out_rows, columns=REQUIRED_OUTPUT_COLS)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out)} moments to {args.out}")

if __name__ == "__main__":
    main()
