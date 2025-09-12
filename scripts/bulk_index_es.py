import argparse, pandas as pd, json, tqdm
from elasticsearch import Elasticsearch, helpers

def make_mapping():
    return {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "default": { "type": "standard" }
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type":"keyword"},
                "sport": {"type":"keyword"},
                "tournament": {"type":"text"},
                "year": {"type":"integer"},
                "event": {"type":"text"},
                "round": {"type":"text"},
                "set": {"type":"integer"},
                "game": {"type":"integer"},
                "point": {"type":"text"},
                "player1": {"type":"text"},
                "player2": {"type":"text"},
                "surface": {"type":"keyword"},
                "source_url": {"type":"keyword"},
                "commentary": {"type":"text"},
                "summary": {"type":"text"},
                "tags": {"type":"text"},
                "text": {"type":"text"}
            }
        }
    }

def main(data_path: str, index_name: str, es_url: str):
    es = Elasticsearch(es_url)  # e.g. http://localhost:9200
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
    es.indices.create(index=index_name, body=make_mapping())

    df = pd.read_csv(data_path)
    actions = ({
        "_op_type": "index",
        "_index": index_name,
        "_id": r["id"],
        "_source": r.to_dict(),
    } for _, r in df.iterrows())
    helpers.bulk(es, actions)
    es.indices.refresh(index=index_name)
    print(f"✓ Indexed {len(df)} docs to '{index_name}'")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--index', default='tennis_moments')
    ap.add_argument('--es-url', default='http://localhost:9200')
    args = ap.parse_args()
    main(args.data, args.index, args.es_url)
