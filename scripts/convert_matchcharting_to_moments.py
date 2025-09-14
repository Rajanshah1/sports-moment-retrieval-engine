
#!/usr/bin/env python3
"""
Convert MatchChartingProject CSVs to moments.csv format.

The MCP CSVs vary; we do robust column detection and build natural-language
commentary from shot/result fields when present.

Example usage:
  python scripts/convert_matchcharting_to_moments.py \
    --mcp_glob "data/external/mcp/*.csv" \
    --out "data/raw/matchcharting_moments.csv"
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
        for c in df.columns:
            if c.lower() == n.lower(): return c
    return None

def normalize_round(r):
    if not r: return ""
    r = str(r).strip()
    mapping = {"F":"Final","SF":"Semi-final","QF":"Quarter-final",
               "R16":"Round of 16","R32":"Round of 32","R64":"Round of 64","R128":"Round of 128"}
    return mapping.get(r, r)

def clean(s): return re.sub(r"[^A-Za-z0-9]+","", str(s))[:12]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcp_glob", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sport", default="tennis")
    ap.add_argument("--event_name", default="Men's Singles")
    args = ap.parse_args()

    files = sorted(glob.glob(args.mcp_glob))
    if not files:
        print(f"No files matched: {args.mcp_glob}", file=sys.stderr); sys.exit(2)

    entries = []
    for f in files:
        try:
            df = pd.read_csv(f)
        except Exception as e:
            print(f"Skip {f}: {e}", file=sys.stderr); continue

        # Common metadata on top rows or columns
        c_tournament = pick(df, ["tournament","tourney_name","event","tournament_name"])
        c_year       = pick(df, ["year","tourney_year","date","tourney_date"])
        c_surface    = pick(df, ["surface"])
        c_round      = pick(df, ["round"])
        c_set        = pick(df, ["set","set_no"])
        c_game       = pick(df, ["game","game_no"])
        c_point      = pick(df, ["point","point_no","rally_index"])
        c_p1         = pick(df, ["player1","p1","p1_name","server","winner"])
        c_p2         = pick(df, ["player2","p2","p2_name","returner","loser"])

        # Shot/result columns (MCP-style)
        c_server     = pick(df, ["server","serving"])
        c_shot       = pick(df, ["shot","shot_type","stroke"])
        c_side       = pick(df, ["side","hand","wing"])         # forehand/backhand
        c_dir        = pick(df, ["direction","dir"])            # dtl/cross/inside-out
        c_winner     = pick(df, ["winner","is_winner","point_winner"])
        c_error      = pick(df, ["error","error_type"])
        c_rally      = pick(df, ["rally","rally_length","rallyCount"])

        tourn = str(df[c_tournament].iloc[0]).strip() if c_tournament else ""
        year  = str(df[c_year].iloc[0]).strip() if c_year else ""
        surface = str(df[c_surface].iloc[0]).strip() if c_surface else ""
        round_h = normalize_round(str(df[c_round].iloc[0]).strip()) if c_round else ""

        p1name = str(df[c_p1].iloc[0]).strip() if c_p1 else ""
        p2name = str(df[c_p2].iloc[0]).strip() if c_p2 else ""

        for i, r in df.iterrows():
            set_no  = r.get(c_set, "")
            game_no = r.get(c_game, "")
            point_no= r.get(c_point, "")

            server = str(r.get(c_server, "")).strip()
            shot   = str(r.get(c_shot, "")).strip()
            side   = str(r.get(c_side, "")).strip()
            direc  = str(r.get(c_dir, "")).strip()
            rally  = str(r.get(c_rally, "")).strip()

            win    = str(r.get(c_winner, "")).strip().lower()
            err    = str(r.get(c_error, "")).strip()

            # Commentary
            bits = []
            if server:
                bits.append(f"{server} serves")
            if side or shot:
                bits.append(f"{side} {shot}".strip())
            if direc:
                bits.append(f"{direc}")
            if rally:
                bits.append(f"after {rally} shots")
            outcome = ""
            if win in {"1","true","yes","winner"}:
                outcome = "wins the point with a clean winner"
            elif err:
                outcome = f"point ends on {err}"
            if outcome:
                bits.append(outcome)
            commentary = ", ".join([b for b in bits if b]) + "." if bits else "Rally recorded."
            summary = "Point won by server." if server == p1name else "Point outcome recorded."

            # Tags
            tags = []
            if "winner" in outcome: tags.append("winner")
            if "error" in outcome or "fault" in outcome: tags.append("error")
            if "backhand" in side.lower(): tags.append("backhand")
            if "forehand" in side.lower(): tags.append("forehand")
            if "dtl" in direc.lower() or "down the line" in direc.lower(): tags.append("down-the-line")
            if "cross" in direc.lower(): tags.append("crosscourt")

            mid = f"mcp_{clean(year)}_{clean(tourn)}_{clean(p1name)}_{clean(p2name)}_{i}"
            entries.append({
                "id": mid,
                "sport": args.sport,
                "tournament": tourn,
                "year": year[:4] if year else "",
                "event": args.event_name,
                "round": round_h,
                "set": set_no,
                "game": game_no,
                "point": point_no if str(point_no) else "Point",
                "player1": p1name,
                "player2": p2name,
                "surface": surface,
                "source_url": "",
                "commentary": commentary,
                "summary": summary,
                "tags": ";".join(tags)
            })

    if not entries:
        print("No entries produced. Check input files/columns.", file=sys.stderr); sys.exit(2)
    out = pd.DataFrame(entries, columns=REQUIRED_OUTPUT_COLS)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Wrote {len(out)} moments to {args.out}")
if __name__ == "__main__":
    main()
