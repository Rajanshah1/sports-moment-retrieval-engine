def render_card(rec: dict) -> str:
    title = f"{rec.get('tournament','')} {rec.get('year','')}: {rec.get('event','')} ({rec.get('round','')})".strip()
    matchup = f"{rec.get('player1','')} vs {rec.get('player2','')}".strip()
    set_game = f"Set {rec.get('set','?')}, Game {rec.get('game','?')}"
    point = rec.get('point','')
    summary = rec.get('summary','')
    tags = rec.get('tags','')
    return f"""### {title}
**Match**: {matchup}  
**Context**: {set_game} — {point}  
**Highlight**: {summary}  
**Tags**: {tags}
"""
