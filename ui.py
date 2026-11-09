"""Gradio demo: Guardrails OFF vs ON side by side, with the raw /guardrail/apply JSON.

Run:  python ui.py   (needs llama-server on :8080 and `uvicorn api:app --port 8000` running)
"""
import json
import os

import gradio as gr
import requests

API = os.environ.get("GUARDRAIL_API", "http://127.0.0.1:8000")
LETTER_NAMES = {"A": "safe", "B": "hate", "C": "insults", "D": "sexual", "E": "violence", "F": "misconduct", "G": "prompt attack"}


def run(message: str):
    if not message.strip():
        return "", "", "", {}
    off = requests.post(f"{API}/chat", json={"message": message, "guardrails": False}, timeout=180).json()
    on = requests.post(f"{API}/chat", json={"message": message, "guardrails": True}, timeout=180).json()
    g = on["guardrail"]["input"]
    scores = g["assessments"][0]["scores"]
    top = max(scores, key=scores.get)
    verdict = f"**{g['action']}** — {g['actionReason']}  \nmodel: {top} {LETTER_NAMES[top]} ({scores[top]:.0%})  \nlatency: {g['assessments'][0]['invocationMetrics']['guardrailProcessingLatency']} ms"
    bars = {f"{L} {LETTER_NAMES[L]}": v for L, v in scores.items()}
    return off["reply"], on["reply"], verdict, bars, json.dumps(g, indent=2)


def load_examples():
    ex = []
    if os.path.exists("demo_prompts.txt"):
        for line in open("demo_prompts.txt", encoding="utf-8"):
            if "\t" in line and not line.startswith("#"):
                ex.append([line.split("\t", 1)[1].strip()])
    return ex


with gr.Blocks(title="local-guardrails") as demo:
    gr.Markdown("# Local guardrails: fine-tuned Qwen3.5-2B + regex PII, AWS ApplyGuardrail API shape")
    msg = gr.Textbox(label="User message", lines=3, placeholder="Type a prompt...")
    btn = gr.Button("Send", variant="primary")
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Guardrails OFF")
            off_out = gr.Textbox(label="model reply (unfiltered)", lines=8)
        with gr.Column():
            gr.Markdown("### Guardrails ON")
            on_out = gr.Textbox(label="reply after guardrail", lines=8)
    verdict = gr.Markdown()
    bars = gr.Label(label="letter probabilities", num_top_classes=7)
    raw = gr.Code(label="POST /guardrail/apply response (AWS shape)", language="json")
    gr.Examples(load_examples(), inputs=msg)
    btn.click(run, inputs=msg, outputs=[off_out, on_out, verdict, bars, raw])
    msg.submit(run, inputs=msg, outputs=[off_out, on_out, verdict, bars, raw])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
