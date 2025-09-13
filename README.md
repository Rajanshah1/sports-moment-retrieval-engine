# Sports Moment Retrieval Engine (Tennis)

Overview & Goal

Build a hybrid IR/NLP system that retrieves iconic tennis moments (lawn & table) from commentary text using BM25 + Sentence‑BERT with a lightweight Gradio UI. Output is a Moment Card with match context, highlight summary, tags, and similar‑moment recommendations.

Key outcomes:

Working CLI + UI, hybrid search, small curated dataset, and evaluation with IR metrics.

Clean, reproducible GitHub repo + final report/slides/video per UNT expectations



## Features
- **Hybrid IR**: BM25 (local) + Sentence-BERT embeddings (semantic) with configurable weights
- **Moment Cards**: tournament, year, round, set/game, short highlight + narrative tags
- **Recommendations**: nearest-neighbor similar moments
- **Gradio UI**: simple search bar → Moment Cards
- **Elasticsearch (optional)**: utilities to create mapping and bulk-index if you prefer an ES backend

## Repo Structure
```
sports-moment-retrieval-engine/
├── README.md
├── requirements.txt
├── config.yaml
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/                # drop raw CSVs here
│   ├── processed/          # normalized moments.csv for indexing
│   └── index/              # local BM25 + FAISS indices
├── docker/
│   └── docker-compose.elasticsearch.yml
├── scripts/
│   ├── prepare_data.py     # raw → processed
│   └── bulk_index_es.py    # (optional) index to Elasticsearch
├── src/smre/
│   ├── __init__.py
│   ├── config.py
│   ├── preprocess.py
│   ├── index_bm25.py
│   ├── embed.py
│   ├── index_elastic.py
│   ├── search.py
│   ├── moment_card.py
│   ├── app.py              # Gradio app
│   └── cli.py              # click CLI (ingest, index, search, serve)
├── tests/
│   └── test_smoke.py
└── docs/
    ├── architecture.md
    └── api.md
```

## Quickstart (Local Hybrid: BM25 + Embeddings)
> Python 3.10+ recommended. A GPU is **not required** (embeddings run on CPU).

```bash
# 1) create & activate env (example with venv)
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) install deps
pip install -r requirements.txt
or
pip install -r requirements.txt -c constraints.txt


# 3) Prepare data (converts raw CSV → processed/moments.csv)
python3 scripts/prepare_data.py --input data/raw/sample_commentary.csv --output data/processed/moments.csv

# 4) Build local indices (BM25 + FAISS)
python3 -m smre.cli index-local --data data/processed/moments.csv --index-dir data/index

# 5) Search from CLI
python3 -m smre.cli search --query "Federer ace championship title 2012" --k 5

# 6) Launch UI
python3 -m smre.cli serve --host 0.0.0.0 --port 7860
```

## Optional: Elasticsearch Backend
- Bring up ES locally (single node) via Docker compose:
```bash
docker compose -f docker/docker-compose.elasticsearch.yml up -d
```
- Index data to ES:
```bash
python scripts/bulk_index_es.py --data data/processed/moments.csv --index tennis_moments
```
- You can then switch `config.yaml` → `backend: elasticsearch` and use the same UI/CLI.



Run Elasticsearch in Docker (skip if not needed now)

From your repo root:

docker compose -f docker/docker-compose.elasticsearch.yml up -d


This will pull and start an ES container (usually on http://localhost:9200).

Check it’s running:

curl http://localhost:9200


You should see version JSON.

## Data Format
Input CSV (raw) columns (example):
- `id, sport, tournament, year, event, round, set, game, point, player1, player2, surface, source_url, commentary, summary, tags`

`prepare_data.py` will normalize and create a `text` field for indexing.

## Notes
- The repository ships with a **tiny sample** dataset (`data/raw/sample_commentary.csv`) purely for demonstration.
  Replace it with real commentary transcripts you have permission to use.
- Sentence-BERT default model: `all-MiniLM-L6-v2`. Change in `config.yaml` if needed.

## Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: Sports Moment Retrieval Engine (Tennis)"
gh repo create yourname/smre-tennis --public --source=. --remote=origin --push
# or set remote manually:
# git remote add origin https://github.com/yourname/smre-tennis.git
# git push -u origin main
```
