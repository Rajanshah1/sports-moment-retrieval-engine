
#!/usr/bin/env python3
"""
Convert Grand Slam point-by-point CSVs to moments.csv format (robust column detection).

Assumes CSVs from Jeff Sackmann's `tennis_slam_pointbypoint` repo or similarly structured PBP data.

Example usage:
  python scripts/convert_slam_pbp_to_moments.py \
    --pbp_glob "data/external/slam_pbp/*.csv" \
    --out "data/raw/tennis_slam_moments.csv"
"""
import argparse, glob, os, re, sys
import pandas as pd

REQUIRED_OUTPUT_COLS = [
    "id","sport","tournament","year","event","round","set","game","point",
    "player1","player2","surface","source_url","commentary","summary","tags"
]

def pick(df, names):
    for n in names:
        if n in df.columns: return n
        # try case-insensitive
        for c in df.columns:
            if c.lower() == n.lower(): return c
    return None

def coalesce(row, keys):
    for k in keys:
        if k in row and pd.notna(row[k]) and str(row[k]).strip():
            return str(row[k]).strip()
    return ""

def build_commentary(r, server, returner, outcome, rally, point_score, set_no, game_no, round_h, tname, year):
    bits = []
    if server or returner:
        if server and returner:
            bits.append(f"{server} serves to {returner}")
        elif server:
            bits.append(f"{server} serves")
    if outcome:
        if bits:
            bits[-1] += f"; {outcome}"
        else:
            bits.append(outcome)
    if rally:
        bits.append(f"after a {rally}-shot rally")
    if point_score:
        bits.append(f"at {point_score}")
    ctx = f" at {tname} {year}" if tname or year else ""
    trail = f". {coalesce(r, ['notes','desc','description'])}" if coalesce(r, ['notes','desc','description']) else ""
    text = ", ".join([b for b in bits if b]) + ctx + "." + trail
    return text.strip()

def build_summary(server, outcome, round_h):
    if round_h and round_h.lower()=="final":
        return f"{server or 'Player'} wins a key point in the Final."
    return f"{server or 'Player'} wins a key point."

def normalize_round(r):
    if not r: return ""
    r = str(r).strip()
    mapping = {"F":"Final","SF":"Semi-final","QF":"Quarter-final",
               "R16":"Round of 16","R32":"Round of 32","R64":"Round of 64","R128":"Round of 128"}
    return mapping.get(r, r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbp_glob", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sport", default="tennis")
    ap.add_argument("--event_name", default="Men's Singles")
    args = ap.parse_args()

    files = sorted(glob.glob(args.pbp_glob))
    if not files:
        print(f"No files matched: {args.pbp_glob}", file=sys.stderr); sys.exit(2)

    rows = []
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"Skip {f}: {e}", file=sys.stderr); continue

        # Detect columns
        c_tournament = pick(df, ["tournament","tourney_name","event","tournament_name"])
        c_year       = pick(df, ["year","tourney_year","date","tourney_date"])
        c_surface    = pick(df, ["surface"])
        c_round      = pick(df, ["round"])
        c_set        = pick(df, ["set","set_no"])
        c_game       = pick(df, ["game","game_no"])
        c_pointno    = pick(df, ["point","point_no","point_index"])
        c_server     = pick(df, ["server","srv","server_name"])
        c_returner   = pick(df, ["returner","ret","returner_name"])
        c_p1         = pick(df, ["player1","p1","p1_name","server","winner"])
        c_p2         = pick(df, ["player2","p2","p2_name","returner","loser"])
        c_score      = pick(df, ["point_score","score","points","score_text"])
        c_outcome    = pick(df, ["outcome","rally_end","result","shot_outcome","winner_shot","point_end"])
        c_rally      = pick(df, ["rally","rally_length","rallyCount"])

        for i, r in df.iterrows():
            tname = str(r.get(c_tournament, "")).strip()
            year  = str(r.get(c_year, "")).strip()
            surface = str(r.get(c_surface, "")).strip()
            round_h = normalize_round(str(r.get(c_round, "")).strip())

            set_no = r.get(c_set, "")
            game_no = r.get(c_game, "")
            point_no = r.get(c_pointno, "")

            server = str(r.get(c_server, "")).strip()
            returner = str(r.get(c_returner, "")).strip()
            player1 = str(r.get(c_p1, "")).strip()
            player2 = str(r.get(c_p2, "")).strip()
            point_score = str(r.get(c_score, "")).strip()
            outcome = str(r.get(c_outcome, "")).strip()
            rally = str(r.get(c_rally, "")).strip()

            # Build commentary/summary
            commentary = build_commentary(r, server, returner, outcome, rally, point_score, set_no, game_no, round_h, tname, year)
            summary = build_summary(server or player1, outcome, round_h)

            # Label point
            point_label = "Point"
            if isinstance(point_score, str) and ("TB" in point_score.upper() or "tie" in point_score.lower()):
                point_label = f"Tie-break Point {point_score}"
            # Heuristic for special points
            tags = []
            if "ace" in outcome.lower():
                tags.append("ace")
            if "double" in outcome.lower() and "fault" in outcome.lower():
                tags.append("double fault")
            if "winner" in outcome.lower():
                tags.append("winner")
            if "break" in outcome.lower():
                tags.append("break point")

            # ID
            def clean(s): return re.sub(r"[^A-Za-z0-9]+","", str(s))[:12]
            mid = f"pbp_{clean(year)}_{clean(tname)}_{clean(player1 or server)}_{clean(player2 or returner)}_{i}"

            rows.append({
                "id": mid,
                "sport": args.sport,
                "tournament": tname,
                "year": year[:4] if year else "",
                "event": args.event_name,
                "round": round_h,
                "set": set_no,
                "game": game_no,
                "point": point_label,
                "player1": player1 or server,
                "player2": player2 or returner,
                "surface": surface,
                "source_url": "",
                "commentary": commentary,
                "summary": summary,
                "tags": ";".join(tags)
            })

    if not rows:
        print("No rows produced. Check your input CSV columns.", file=sys.stderr); sys.exit(2)

    out = pd.DataFrame(rows, columns=REQUIRED_OUTPUT_COLS)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out)} moments to {args.out}")
if __name__ == "__main__":
    main()
