import json
import pathlib
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from nltk.tokenize import wordpunct_tokenize

from .config import load_config
from .index_bm25 import build_bm25, save_bm25, load_bm25
from .embed import build_embeddings, save_faiss, load_faiss
from .index_elastic import make_es_client, es_search


# ------------------------------- helpers ------------------------------------ #

def _minmax(x: np.ndarray) -> np.ndarray:
    """Min–max normalize (safe for all-constant, NaN, or negative vectors)."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return x
    mn = float(np.nanmin(x))
    mx = float(np.nanmax(x))
    if not np.isfinite(mn) or not np.isfinite(mx) or mx - mn <= 1e-12:
        return np.zeros_like(x, dtype=float)
    return (x - mn) / (mx - mn)


def _safe_str_series(s: pd.Series) -> pd.Series:
    """Lowercase string series safely (handles NaNs / non-strings)."""
    return s.astype(str).str.lower()


def _apply_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """
    Apply simple filters:
      - years: exact match on 'year' column (if present)
      - stages: substring match against 'round' and 'point' columns (if present)
    """
    out = df

    # Years (keep only reasonable 4-digit ints)
    years = filters.get("years") or []
    if len(years) > 0 and "year" in out.columns:
        years = [y for y in years if isinstance(y, int) and 1900 <= y <= 2100]
        if len(years) > 0:
            out = out[out["year"].isin(years)]

    # Stages (substring match against round/point)
    stages = [s.lower() for s in (filters.get("stages") or [])]
    if len(stages) > 0 and any(c in out.columns for c in ("round", "point")):
        mask = None
        if "round" in out.columns:
            r = _safe_str_series(out["round"])
            for st in stages:
                m = r.str.contains(st, na=False)
                mask = m if mask is None else (mask | m)
        if "point" in out.columns:
            p = _safe_str_series(out["point"])
            for st in stages:
                m = p.str.contains(st, na=False)
                mask = m if mask is None else (mask | m)
        if mask is not None:
            out = out[mask]

    return out


# ------------------------------- indexing ----------------------------------- #

def build_local_indices(
    data_csv: str,
    index_dir: str,
    model_name: str,
    batch_size: int = 64,
) -> None:
    """
    Build BM25 + embedding index from a local CSV.
      - data_csv must contain 'id' and 'text' columns
      - index_dir will receive bm25.pkl, ids.json, faiss files, and meta.json
    """
    df = pd.read_csv(data_csv)
    if "id" not in df.columns or "text" not in df.columns:
        raise ValueError("data CSV must contain 'id' and 'text' columns")

    texts = df["text"].fillna("").astype(str).tolist()
    ids = df["id"].astype(str).tolist()

    # BM25
    bm25, tok = build_bm25(texts)
    save_bm25(bm25, tok, ids, index_dir)

    # Embeddings (Sentence-Transformers) + FAISS
    embs = build_embeddings(texts, model_name, batch_size)
    save_faiss(embs, ids, index_dir)

    # meta
    pathlib.Path(index_dir).mkdir(parents=True, exist_ok=True)
    (pathlib.Path(index_dir) / "meta.json").write_text(json.dumps({"n_docs": len(df)}))

    print(f"Built indices for {len(df)} docs → {index_dir}")


# ------------------------------- search ------------------------------------- #

def hybrid_search(
    query: str,
    k: int = 10,
    cfg: Optional[Dict] = None,
    data_csv: str = "data/processed/moments.csv",
) -> List[Dict]:
    """
    Hybrid search:
      - If cfg['backend'] == 'elasticsearch': query ES index
      - Else: local hybrid over BM25 + FAISS embeddings with configurable weights
    Returns a list of dict rows (top-k).
    """
    # Lazy import so `index-local` doesn’t fail when preprocess is absent/minimal
    try:
        from .preprocess import normalize_query, extract_filters  # type: ignore
    except Exception:
        def normalize_query(s: str) -> str:  # fallback
            return s.strip()
        def extract_filters(_: str) -> Dict:
            return {}

    cfg = cfg or load_config()
    q = normalize_query(query)
    filters = extract_filters(q)

    # ------------------------ Elasticsearch backend ------------------------- #
    if cfg.get("backend") == "elasticsearch":
        es = make_es_client()
        hits = es_search(es, cfg["index_name"], q, k * 2)
        df_es = pd.DataFrame(hits)
        df_es = _apply_filters(df_es, filters)
        return df_es.head(k).to_dict(orient="records")

    # -------------------------- Local hybrid backend ------------------------ #
    df = pd.read_csv(data_csv)
    if "id" not in df.columns:
        raise ValueError("data CSV must contain 'id' column")
    ids_df = df["id"].astype(str).tolist()

    # --- BM25 --- #
    bm25, tokenized, ids_b = load_bm25(cfg["local"]["index_dir"])
    qtok = wordpunct_tokenize(q.lower())  # no NLTK 'punkt' download needed
    bm25_scores = bm25.get_scores(qtok)

    # map doc_id -> row index (as strings to avoid dtype mismatches)
    id_to_row = {doc_id: i for i, doc_id in enumerate(ids_df)}

    bm25_vec = np.zeros(len(df), dtype=float)
    for i, doc_id in enumerate(map(str, ids_b)):
        j = id_to_row.get(doc_id)
        if j is not None:
            bm25_vec[j] = float(bm25_scores[i])

    # --- Embeddings / FAISS --- #
    import faiss  # local import to keep optional dep optional
    from sentence_transformers import SentenceTransformer

    index, embs, ids_e = load_faiss(cfg["local"]["index_dir"])
    model = SentenceTransformer(cfg["embedding"]["model_name"])
    qemb = model.encode([q], normalize_embeddings=True)

    D, I = index.search(np.asarray(qemb, dtype="float32"), len(df))
    embed_vec = np.zeros(len(df), dtype=float)
    for rank, ridx in enumerate(I[0]):
        if ridx < 0:
            continue
        doc_id = str(ids_e[ridx])
        j = id_to_row.get(doc_id)
        if j is not None:
            embed_vec[j] = float(D[0][rank])

    # --- Combine with min–max normalization --- #
    a = float(cfg["hybrid"]["alpha_bm25"])
    b = float(cfg["hybrid"]["beta_embed"])
    scores = a * _minmax(bm25_vec) + b * _minmax(embed_vec)

    df_scores = df.copy()
    df_scores["score"] = scores

    # Apply filters and sort
    filtered = _apply_filters(df_scores, filters).sort_values("score", ascending=False).head(k)

    # Soft fallback: if filters removed everything, return top-k unfiltered
    if len(filtered) == 0:
        return df_scores.sort_values("score", ascending=False).head(k).to_dict(orient="records")

    return filtered.to_dict(orient="records")

