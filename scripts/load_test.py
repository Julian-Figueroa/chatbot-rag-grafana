"""
Generate load against the /chat endpoint to populate Grafana dashboards.
Run: python scripts/load_test.py [--url http://localhost:8000] [--n 30]
"""
import argparse
import time
import random
import httpx

QUESTIONS = [
    "What is Grafana Loki?",
    "How do I create a dashboard in Grafana?",
    "What data sources does Grafana support?",
    "How does Grafana alerting work?",
    "What is Grafana Tempo used for?",
    "How do I configure Prometheus as a data source?",
    "What are Grafana variables?",
    "How do I share a Grafana dashboard?",
    "What is the difference between Grafana OSS and Enterprise?",
    "How do I use Grafana Explore?",
    "What are Grafana annotations?",
    "How do I set up Grafana provisioning?",
    "What is LogQL?",
    "How do I configure Grafana alerting notifications?",
    "What panel types are available in Grafana?",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    args = parser.parse_args()

    print(f"Sending {args.n} requests to {args.url}/chat ...")
    success, errors = 0, 0

    for i in range(args.n):
        q = random.choice(QUESTIONS)
        try:
            r = httpx.post(f"{args.url}/chat", json={"question": q}, timeout=60.0)
            if r.status_code == 200:
                tokens = r.json().get("tokens_used", "?")
                print(f"[{i+1}/{args.n}] OK — tokens={tokens} — q={q[:50]}")
                success += 1
            else:
                print(f"[{i+1}/{args.n}] HTTP {r.status_code} — {r.text[:80]}")
                errors += 1
        except Exception as e:
            print(f"[{i+1}/{args.n}] ERROR — {e}")
            errors += 1

        if i < args.n - 1:
            time.sleep(args.delay)

    print(f"\nDone. Success: {success}, Errors: {errors}")


if __name__ == "__main__":
    main()
