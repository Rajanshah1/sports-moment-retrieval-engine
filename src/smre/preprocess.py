import re

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b", re.IGNORECASE)

# map query words to the normalized stage token present in your data ("final", "semi", "quarter")
_STAGE_SYNONYMS = [
    (["championship", "title", "finals", "grand final", "final"], "final"),
    (["semi", "semifinal", "semi-final", "sf"], "semi"),
    (["quarter", "quarterfinal", "quarter-final", "qf"], "quarter"),
]

def extract_filters(q: str) -> dict:
    ql = q.lower()

    # 4-digit years: use group(0) so we don't capture just "20"
    years = [int(m.group(0)) for m in _YEAR_RE.finditer(ql)]

    # normalize stage tokens from many synonyms down to your column’s vocabulary
    stages = set()
    for variants, normalized in _STAGE_SYNONYMS:
        if any(v in ql for v in variants):
            stages.add(normalized)

    return {"years": years, "stages": sorted(stages)}

