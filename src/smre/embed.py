import numpy as np, pathlib, json
from sentence_transformers import SentenceTransformer
import faiss

def build_embeddings(texts: list[str], model_name: str, batch_size: int = 64):
    model = SentenceTransformer(model_name)
    embs = model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)
    return np.asarray(embs, dtype='float32')

def save_faiss(embs: np.ndarray, ids: list[str], index_dir: str):
    out = pathlib.Path(index_dir)
    out.mkdir(parents=True, exist_ok=True)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine if normalized
    index.add(embs)
    faiss.write_index(index, str(out / 'faiss.index'))
    np.save(out / 'embeddings.npy', embs)
    (out / 'ids.json').write_text(json.dumps(ids))

def load_faiss(index_dir: str):
    out = pathlib.Path(index_dir)
    index = faiss.read_index(str(out / 'faiss.index'))
    ids = json.loads((out / 'ids.json').read_text())
    embs = np.load(out / 'embeddings.npy')
    return index, embs, ids
