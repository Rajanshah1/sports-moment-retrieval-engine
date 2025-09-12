from .config import load_config
from .preprocess import normalize_query, extract_filters
from .index_bm25 import build_bm25, save_bm25, load_bm25
from .embed import build_embeddings, save_faiss, load_faiss
from .index_elastic import make_es_client, es_search
import pandas as pd, numpy as np, pathlib, json, math

def _apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df
    if filters.get('years'):
        out = out[out['year'].isin(filters['years'])]
    # simple stage filter by substring in point/round columns
    for st in filters.get('stages', []):
        out = out[out['point'].str.lower().str.contains(st) | out['round'].str.lower().str.contains(st)]
    return out

def build_local_indices(data_csv: str, index_dir: str, model_name: str, batch_size: int = 64):
    df = pd.read_csv(data_csv)
    texts = df['text'].fillna('').tolist()
    ids = df['id'].tolist()
    bm25, tok = build_bm25(texts)
    save_bm25(bm25, tok, ids, index_dir)
    embs = build_embeddings(texts, model_name, batch_size)
    save_faiss(embs, ids, index_dir)
    (pathlib.Path(index_dir)/'meta.json').write_text(json.dumps({'n_docs': len(df)}))
    print(f"Built indices for {len(df)} docs → {index_dir}")

def hybrid_search(query: str, k: int = 10, cfg: dict | None = None, data_csv: str = 'data/processed/moments.csv'):
    cfg = cfg or load_config()
    q = normalize_query(query)
    filters = extract_filters(q)
    if cfg['backend'] == 'elasticsearch':
        es = make_es_client()
        hits = es_search(es, cfg['index_name'], q, k*2)
        df = pd.DataFrame(hits)
        df = _apply_filters(df, filters)
        return df.head(k).to_dict(orient='records')

    # local hybrid
    df = pd.read_csv(data_csv)
    df_f = _apply_filters(df, filters)
    # load BM25
    bm25, tokenized, ids_b = load_bm25(cfg['local']['index_dir'])
    # BM25 scores
    from nltk.tokenize import word_tokenize
    qtok = word_tokenize(q.lower())
    bm25_scores = bm25.get_scores(qtok)
    # reorder to match df ordering; we need a mapping from ids_b order to df rows
    id_to_row = {row_id: i for i, row_id in enumerate(df['id'].tolist())}
    bm25_vec = np.zeros(len(df), dtype=float)
    for i, doc_id in enumerate(ids_b):
        bm25_vec[id_to_row[doc_id]] = bm25_scores[i]

    # Embedding scores via FAISS inner product
    import faiss, numpy as np
    from sentence_transformers import SentenceTransformer
    index, embs, ids_e = load_faiss(cfg['local']['index_dir'])
    model = SentenceTransformer(cfg['embedding']['model_name'])
    qemb = model.encode([q], normalize_embeddings=True)
    D, I = index.search(np.asarray(qemb, dtype='float32'), len(df))
    embed_vec = np.zeros(len(df), dtype=float)
    for rank, row_idx in enumerate(I[0]):
        if row_idx < 0: continue
        doc_id = ids_e[row_idx]
        embed_vec[id_to_row[doc_id]] = float(D[0][rank])

    # Combine
    a = cfg['hybrid']['alpha_bm25']
    b = cfg['hybrid']['beta_embed']
    scores = a * (bm25_vec / (bm25_vec.max() or 1)) + b * (embed_vec / (embed_vec.max() or 1))

    df_scores = df.copy()
    df_scores['score'] = scores
    # apply filters post-scoring to remain simple
    df_scores = _apply_filters(df_scores, filters)
    df_scores = df_scores.sort_values('score', ascending=False).head(k)
    return df_scores.to_dict(orient='records')
