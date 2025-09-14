import pandas as pd, numpy as np, json, argparse
from smre.search import hybrid_search


def precision_at_k(ranked, rel, k=5):
return sum(1 for d in ranked[:k] if d in rel) / k


def mrr(ranked, rel):
for i,d in enumerate(ranked,1):
if d in rel: return 1/i
return 0.0


def main():
ap = argparse.ArgumentParser()
ap.add_argument('--queries', default='evaluation/queries.csv')
ap.add_argument('--qrels', default='evaluation/qrels.csv')
ap.add_argument('--k', type=int, default=5)
args = ap.parse_args()


Q = pd.read_csv(args.queries)
qr = pd.read_csv(args.qrels)
rel = {q: set(m.docid for _,m in g.iterrows()) for q,g in qr.groupby('qid')}


rows = []
for _, row in Q.iterrows():
qid, qtext = row['qid'], row['query']
results = hybrid_search(qtext, k=args.k)
ranked = [r['id'] for r in results]
rows.append({
'qid': qid,
'P@%d'%args.k: precision_at_k(ranked, rel.get(qid,set()), args.k),
'MRR': mrr(ranked, rel.get(qid,set()))
})
df = pd.DataFrame(rows)
print(df)
print('\nAverages:')
print(df.mean(numeric_only=True))


if __name__ == '__main__':
main()
