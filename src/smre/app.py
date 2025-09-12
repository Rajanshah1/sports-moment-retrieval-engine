import gradio as gr
from .config import load_config
from .search import hybrid_search
from .moment_card import render_card

def _search(query, k):
    cfg = load_config()
    results = hybrid_search(query, k=int(k), cfg=cfg)
    if not results:
        return "No results."
    md = "\n\n".join(render_card(r) for r in results)
    return md

def main():
    cfg = load_config()
    with gr.Blocks(title=cfg['ui']['title']) as demo:
        gr.Markdown(f"# {cfg['ui']['title']}")
        with gr.Row():
            query = gr.Textbox(label="Describe the moment", placeholder="e.g., Federer ace championship title 2012")
            k = gr.Slider(1, 20, value=5, step=1, label="Top K")
        output = gr.Markdown()
        btn = gr.Button("Search") 
        btn.click(_search, inputs=[query, k], outputs=[output])
    demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == '__main__':
    main()
