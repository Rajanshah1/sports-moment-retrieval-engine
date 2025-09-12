# Architecture

## Pipeline
1. **Data Ingestion** → CSV commentary + metadata
2. **Preprocess** → build `text` field
3. **Indexing (Local)** → BM25 (rank-bm25) + SBERT embeddings (FAISS)
4. **Hybrid Search** → combine BM25 and embedding scores
5. **Moment Cards** → render top-K results + recommendations (nearest neighbors)

## Scoring
`score = α * BM25_norm + β * Embed_norm` where α, β from `config.yaml`.

## Backends
- **Local** (default): files under `data/index/`
- **Elasticsearch** (optional): multi_match query across commentary/summary/text
