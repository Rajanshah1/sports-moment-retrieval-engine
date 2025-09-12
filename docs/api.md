# Developer API

### Command Line
- `python -m smre.cli index-local --data data/processed/moments.csv`
- `python -m smre.cli search --query "Federer ace championship title 2012" --k 5`
- `python -m smre.cli serve`

### Python
```python
from smre.search import hybrid_search
res = hybrid_search("Federer ace championship title 2012", k=5)
```

### Gradio
`python -m smre.cli serve` → open http://localhost:7860
