import re

def normalize_query(q: str) -> str:
    return re.sub(r'\s+', ' ', q.strip())

def extract_filters(q: str):
    # very light heuristics to detect year and common stages
    years = re.findall(r'(19|20)\d{2}', q)
    stages = []
    for s in ['final','semi','quarter','championship','championship point','break point']:
        if s in q.lower():
            stages.append(s)
    return {'years': [int(y) for y in years], 'stages': stages}
