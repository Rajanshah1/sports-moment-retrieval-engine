import json, pickle, pathlib
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import nltk
nltk.download('punkt', quiet=True)

def build_bm25(texts: list[str]):
    tokenized = [word_tokenize(t.lower()) for t in texts]
    bm25 = BM25Okapi(tokenized)
    return bm25, tokenized

def save_bm25(bm25, tokenized_docs, ids, out_dir: str):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'bm25.pkl', 'wb') as f:
        pickle.dump({'bm25': bm25, 'tokenized': tokenized_docs}, f)
    (out / 'ids.json').write_text(json.dumps(ids))

def load_bm25(index_dir: str):
    with open(pathlib.Path(index_dir) / 'bm25.pkl', 'rb') as f:
        obj = pickle.load(f)
    ids = json.loads((pathlib.Path(index_dir) / 'ids.json').read_text())
    return obj['bm25'], obj['tokenized'], ids
