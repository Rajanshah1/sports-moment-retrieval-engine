import pandas as pd
import argparse, pathlib

def main(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    # create normalized text column for indexing (mix of commentary, summary & metadata)
    parts = [
        df['commentary'].fillna(''),
        df['summary'].fillna(''),
        df['tournament'].fillna(''),
        df['event'].fillna(''),
        df['round'].astype(str).fillna(''),
        df['player1'].fillna(''),
        df['player2'].fillna(''),
        df['tags'].fillna(''),
        df['surface'].fillna(''),
        df['year'].astype(str).fillna('')
    ]
    df['text'] = (' . '.join(['{}'] * len(parts))).format(*parts)  # interleave with separators
    # simple schema cleanup
    keep = ['id','sport','tournament','year','event','round','set','game','point','player1','player2','surface','source_url','commentary','summary','tags','text']
    df = df[keep]
    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"✓ Wrote {len(df)} rows to {out}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    main(args.input, args.output)
