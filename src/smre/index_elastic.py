from elasticsearch import Elasticsearch

def make_es_client(url='http://localhost:9200'):
    return Elasticsearch(url)

def es_search(es, index: str, query: str, k: int = 10):
    body = {
        "size": k,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["commentary^2", "summary^1.5", "text"]
            }
        }
    }
    res = es.search(index=index, body=body)
    hits = res['hits']['hits']
    return [h['_source'] | {'_score': h['_score'], '_id': h['_id']} for h in hits]
