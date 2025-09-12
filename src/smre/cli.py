import click
from .config import load_config
from .search import build_local_indices, hybrid_search
from rich import print

@click.group()
def cli():
    pass

@cli.command('index-local')
@click.option('--data', default='data/processed/moments.csv')
@click.option('--index-dir', default='data/index')
@click.option('--model', default=None, help='SBERT model (overrides config)')
@click.option('--batch-size', default=64)
def index_local(data, index_dir, model, batch_size):
    cfg = load_config()
    model_name = model or cfg['embedding']['model_name']
    build_local_indices(data, index_dir, model_name, batch_size)

@cli.command('search')
@click.option('--query', required=True)
@click.option('--k', default=5)
@click.option('--data', default='data/processed/moments.csv')
def do_search(query, k, data):
    cfg = load_config()
    res = hybrid_search(query, k=k, cfg=cfg, data_csv=data)
    for i, r in enumerate(res, 1):
        print(f"[bold]{i}.[/bold] {r.get('tournament','')} {r.get('year','')} — {r.get('player1','')} vs {r.get('player2','')} | {r.get('point','')} | score={r.get('score',''):.3f}")
        print(f"    {r.get('summary','')}")

@cli.command('serve')
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=7860, type=int)
def serve(host, port):
    import uvicorn, os
    os.environ.setdefault('GRADIO_SERVER_NAME', host)
    os.environ.setdefault('GRADIO_SERVER_PORT', str(port))
    from .app import main
    main()

if __name__ == '__main__':
    cli()
