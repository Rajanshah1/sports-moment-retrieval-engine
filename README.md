# Sports Moment Retrieval Engine (Tennis)

<<<<<<< HEAD
Overview & Goal

Build a hybrid IR/NLP system that retrieves iconic tennis moments (lawn & table) from commentary text using BM25 + Sentence‑BERT with a lightweight Gradio UI. Output is a Moment Card with match context, highlight summary, tags, and similar‑moment recommendations.

Key outcomes:

Working CLI + UI, hybrid search, small curated dataset, and evaluation with IR metrics.

Clean, reproducible GitHub repo + final report/slides/video per UNT expectations


=======
Find iconic tennis moments (e.g., _“Federer Wimbledon final championship point”_) using a **hybrid** search that combines **BM25** (exact keywords) and **sentence‑embedding similarity** (semantic meaning). The system returns concise **Moment Cards** with summary, tags, and (optionally) a link to the source.
>>>>>>> a53f8c2 (Ignore external data repos)

---

## ✨ Features
- **Hybrid retrieval**: `score = α·BM25 + β·cosine(embeddings)`
- **Embeddings** via Sentence‑Transformers (SBERT) + **FAISS** vector index
- **CLI + Gradio UI**: index locally, search from terminal, or launch a simple web app
- **Data prep scripts** to convert popular tennis datasets into a unified `moments.csv`

---

## 🧠 How it works (overview)

```
Query
  ├─▶ BM25 Retriever (top‑K) ──┐
  │                            │
  └─▶ Embedding Index (top‑K) ─┴─▶ Candidate Union ─▶ Hybrid Scorer (α·BM25 + β·CosSim)
                                                      └─▶ (Optional) BERT cross‑encoder re‑rank
                                                               └─▶ Moment Cards
```

**Why hybrid?**  
BM25 nails exact quotes/keywords. Embeddings catch paraphrases like “last serve to win the final” ≈ “championship point”. Together they improve both precision and recall.

---

## ✅ Requirements

> **Recommended:** Python **3.11** (PyTorch/FAISS work smoothly).  
> Python 3.13 will likely cause dependency conflicts for `torch/sentence-transformers`.

- macOS or Linux
- Python 3.11
- (Optional) Homebrew (`brew`) for convenience tools

---

## 🚀 Quickstart

### 1) Create and activate a Python 3.11 virtual env
```bash
# Install Python 3.11 if needed (macOS)
brew install python@3.11

# From repo root:
python3.11 -m venv .venv
source .venv/bin/activate
python -V   # should show 3.11.x
pip install --upgrade pip
```

### 2) Install dependencies (using a constraints file)
Create `constraints.txt` in the project root (pinned, compatible stack):

```txt
# Core numeric/science
numpy==1.26.4
scipy==1.11.4
scikit-learn==1.4.2
pandas==2.2.2

# IR / NLP
rank-bm25==0.2.2
nltk==3.9.1
transformers==4.45.2

# Sentence embeddings + deps
sentence-transformers==3.0.1
torch==2.3.1

# Vector index
faiss-cpu==1.8.0.post5

# App / CLI / UI
gradio==4.44.0
click==8.1.7
rich==13.7.1
tqdm==4.66.4
python-dotenv==1.0.1
PyYAML==6.0.1
packaging==24.0
```

Then install:
```bash
pip install -r requirements.txt -c constraints.txt
# or: pip install -r constraints.txt
```

### 3) Install the package (for clean CLI imports)
```bash
pip install -e .
```

---

## 📦 Data

### Input sources (any subset is fine)
- **Jeff Sackmann ATP matches** (`atp_matches_YYYY.csv`)
- **Match Charting Project** (point‑level; CSVs)
- **Grand Slams point‑by‑point** (Jeff Sackmann)

Put raw files under:
```
data/
  external/
    atp/            # Sackmann matches
    mcp/            # Match Charting Project
    slam_pbp/       # Slam point-by-point
  raw/
  processed/
  index/
```

### Convert to moments

**A) ATP matches → synthetic “match point” moments**
```bash
python scripts/convert_sackmann_to_moments.py   --matches_glob "data/external/atp/*.csv"   --out "data/raw/atp_matches_moments.csv"
```

**B) Match Charting Project → moments**
```bash
python scripts/convert_matchcharting_to_moments.py   --mcp_glob "data/external/mcp/*.csv"   --out "data/raw/matchcharting_moments.csv"
```

**C) Grand Slams PBP → moments**
```bash
python scripts/convert_slam_pbp_to_moments.py   --pbp_glob "data/external/slam_pbp/*.csv"   --out "data/raw/tennis_slam_moments.csv"
```

**D) (Optional) Your own sample commentary**
```bash
python scripts/prepare_data.py   --input data/raw/sample_commentary.csv   --output data/processed/moments.csv
```

> You can also **concatenate** multiple raw moment CSVs (A/B/C) and feed them into `prepare_data.py` if needed.

---

## ⚙️ Configuration

`config.yaml` (example keys):
```yaml
index:
  dir: "data/index"
  top_k: 50

embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dim: 384

hybrid:
  alpha_bm25: 0.5   # weight for BM25 (0..1)
  beta_embed: 0.5   # weight for embeddings (0..1)

ui:
  host: "0.0.0.0"
  port: 7860
```

---

## 🔎 Build index & search

### 1) Prepare processed data
If your converter already produced a `moments.csv`, you can skip this. Otherwise:
```bash
python scripts/prepare_data.py   --input data/raw/atp_matches_moments.csv   --output data/processed/moments.csv
```

### 2) Build indices (BM25 + FAISS)
```bash
python -m smre.cli index-local   --data data/processed/moments.csv   --index-dir data/index
```

### 3) Search from CLI
```bash
python -m smre.cli search   --query "Federer Wimbledon final championship point"   --k 5
```

### 4) Launch the UI
```bash
python -m smre.cli serve --host 0.0.0.0 --port 7860
# open http://localhost:7860
```

---

## 🧪 Evaluation (optional)
- Provide a small `evaluation/queries.csv` and `evaluation/qrels.csv`
- Compute metrics (P@5, MRR, nDCG@5)
- Sweep `alpha_bm25` / `beta_embed` to see sensitivity

---

## 📁 Project layout (expected)
```
.
├── config.yaml
├── constraints.txt
├── data/
│   ├── external/{atp,mcp,slam_pbp}/
│   ├── raw/
│   ├── processed/
│   └── index/
├── docker/
├── docs/
├── notebooks/
├── README.md
├── requirements.txt
├── scripts/
│   ├── convert_sackmann_to_moments.py
│   ├── convert_matchcharting_to_moments.py
│   ├── convert_slam_pbp_to_moments.py
│   └── prepare_data.py
├── src/
│   └── smre/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── search.py
│       ├── bm25_backend.py
│       ├── embed_backend.py
│       └── app.py
└── tests/
```

---

## 🛠️ Troubleshooting

**`ModuleNotFoundError: No module named 'smre'`**  
→ Run from project root and install the package:
```bash
<<<<<<< HEAD
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
=======
pip install -e .
# or: PYTHONPATH=src python -m smre.cli ...
>>>>>>> a53f8c2 (Ignore external data repos)
```

**`No module named 'yaml'`**  
→ Install dependencies:
```bash
pip install -r requirements.txt -c constraints.txt
```

**`DtypeWarning: mixed types … set low_memory=False`**  
→ Safe to ignore. Or read CSV with:
```python
pd.read_csv(path, low_memory=False)
```
and normalize columns with `astype("string").fillna("")`.

<<<<<<< HEAD


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
=======
**`ResolutionImpossible` / torch not found**  
→ Use Python **3.11** and the pinned **constraints.txt** above.
>>>>>>> a53f8c2 (Ignore external data repos)

**`zsh: command not found: python`**  
→ Use `python3` or ensure your venv is activated: `source .venv/bin/activate`.

**`tree: command not found`**  
→ `brew install tree` or use `find . -maxdepth 2 -print`.

---

## 🔐 Notes on data sources
This project supports community datasets (e.g., Jeff Sackmann, Match Charting Project). Respect each dataset’s license/terms of use and provide attribution where required.

---

## 🧭 Roadmap
- Cross‑encoder **BERT re‑ranker** for top‑N
- Entity‑aware search (players, tournaments, surfaces)
- Query spell‑correction and suggestions
- Docker compose for UI + persistent indices

---

## 🤝 Contributing
PRs welcome! Please:
1. Open an issue describing the change.
2. Add tests if applicable.
3. Keep code style consistent with the repo.

---

## 📄 License
This project is released under the **MIT License** (see `LICENSE`).
