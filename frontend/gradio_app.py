import os
import httpx
import gradio as gr
import gradio.networking

# Gradio 4.x performs a localhost reachability check after launch that fails
# inside Docker containers. This bypasses it.
gradio.networking.url_ok = lambda url: True

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def chat(message: str, history: list) -> str:
    try:
        response = httpx.post(
            f"{BACKEND_URL}/chat",
            json={"question": message, "session_id": "gradio"},
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


demo = gr.ChatInterface(
    fn=chat,
    title="Grafana RAG Chatbot",
    description=(
        "Ask questions about Grafana — dashboards, data sources, alerting, Loki, "
        "Prometheus, and more. Powered by GPT-4o-mini + ChromaDB."
    ),
    examples=[
        "What is Grafana Loki?",
        "How do I create a dashboard in Grafana?",
        "What data sources does Grafana support?",
        "How does Grafana alerting work?",
        "What is the difference between Grafana OSS and Grafana Enterprise?",
    ],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
