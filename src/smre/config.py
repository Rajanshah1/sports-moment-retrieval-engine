import yaml, pathlib

def load_config(path: str | None = None) -> dict:
    cfg_path = pathlib.Path(path or 'config.yaml')
    with cfg_path.open('r') as f:
        return yaml.safe_load(f)
