import os
import httpx

# Jinja2 3.1.x includes env.globals (a dict) in the template cache key, making
# the key unhashable. Patch LRUCache to skip caching for unhashable keys so
# Gradio 4.x templates load correctly.
import jinja2.utils as _jinja2_utils

_orig_lru_getitem = _jinja2_utils.LRUCache.__getitem__
_orig_lru_setitem = _jinja2_utils.LRUCache.__setitem__

def _safe_lru_getitem(self, key):
    try:
        return _orig_lru_getitem(self, key)
    except TypeError:
        raise KeyError(key)

def _safe_lru_setitem(self, key, value):
    try:
        _orig_lru_setitem(self, key, value)
    except TypeError:
        pass

_jinja2_utils.LRUCache.__getitem__ = _safe_lru_getitem
_jinja2_utils.LRUCache.__setitem__ = _safe_lru_setitem

import gradio as gr
import gradio.networking

# Gradio 4.x performs a localhost reachability check after launch that fails
# inside Docker containers. This bypasses it.
gradio.networking.url_ok = lambda url: True

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-key-123")
HEADERS = {"X-API-Key": API_KEY}


def chat(message: str, history: list) -> str:
    try:
        response = httpx.post(
            f"{BACKEND_URL}/chat",
            json={"question": message, "session_id": "gradio"},
            headers=HEADERS,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        answer = data["answer"]
        sources = data.get("sources", [])
        tokens = data.get("tokens_used", 0)
        if sources:
            source_list = "\n".join(f"- `{s}`" for s in sources)
            answer += f"\n\n**Sources:**\n{source_list}"
        if tokens:
            answer += f"\n\n*Tokens used: {tokens}*"
        return answer
    except httpx.HTTPStatusError as e:
        return f"Backend error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error: {e}"


def send_feedback(rating: str) -> str:
    try:
        httpx.post(
            f"{BACKEND_URL}/feedback",
            params={"session_id": "gradio", "rating": rating},
            headers=HEADERS,
            timeout=5.0,
        )
        return "Thanks for the feedback!"
    except Exception:
        return "Feedback could not be recorded."


with gr.Blocks(title="Grafana RAG Chatbot") as demo:
    gr.Markdown(
        "# Grafana RAG Chatbot\n"
        "Ask questions about Grafana — dashboards, data sources, alerting, Loki, "
        "Prometheus, and more. Powered by GPT-4o-mini + ChromaDB."
    )

    gr.ChatInterface(
        fn=chat,
        examples=[
            "What is Grafana Loki?",
            "How do I create a dashboard in Grafana?",
            "What data sources does Grafana support?",
            "How does Grafana alerting work?",
            "What is the difference between Grafana OSS and Grafana Enterprise?",
        ],
    )

    gr.Markdown("### Was the last response helpful?")
    feedback_status = gr.Markdown("")
    with gr.Row():
        up_btn = gr.Button("👍 Helpful", variant="primary")
        down_btn = gr.Button("👎 Not helpful", variant="secondary")

    up_btn.click(fn=lambda: send_feedback("up"), outputs=feedback_status)
    down_btn.click(fn=lambda: send_feedback("down"), outputs=feedback_status)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
