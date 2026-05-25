"""
Downloads ~60 Grafana .md doc files from the grafana/grafana GitHub repo into data/docs/.
Run from project root: python scripts/download_docs.py

Paths verified against grafana/grafana main branch structure (May 2026).
"""
import os
import urllib.request

# Each entry is the path in the grafana/grafana repo (main branch)
DOCS = [
    # Introduction
    "docs/sources/introduction/_index.md",
    "docs/sources/introduction/grafana-enterprise.md",
    "docs/sources/introduction/grafana-cloud.md",
    # Fundamentals
    "docs/sources/fundamentals/_index.md",
    "docs/sources/fundamentals/dashboards-overview/_index.md",
    "docs/sources/fundamentals/timeseries/_index.md",
    "docs/sources/fundamentals/intro-to-prometheus/_index.md",
    "docs/sources/fundamentals/getting-started/_index.md",
    # Data sources
    "docs/sources/datasources/_index.md",
    "docs/sources/datasources/prometheus/_index.md",
    "docs/sources/datasources/prometheus/query-editor/_index.md",
    "docs/sources/datasources/loki/_index.md",
    "docs/sources/datasources/loki/configure-loki-data-source.md",
    "docs/sources/datasources/loki/query-editor/_index.md",
    "docs/sources/datasources/tempo/_index.md",
    "docs/sources/datasources/elasticsearch/_index.md",
    "docs/sources/datasources/influxdb/_index.md",
    "docs/sources/datasources/mysql/_index.md",
    "docs/sources/datasources/postgres/_index.md",
    # Alerting
    "docs/sources/alerting/_index.md",
    "docs/sources/alerting/fundamentals/_index.md",
    "docs/sources/alerting/alerting-rules/_index.md",
    "docs/sources/alerting/configure-notifications/_index.md",
    "docs/sources/alerting/set-up/_index.md",
    # Visualizations / panels
    "docs/sources/visualizations/_index.md",
    "docs/sources/visualizations/panels-visualizations/_index.md",
    "docs/sources/visualizations/dashboards/_index.md",
    "docs/sources/visualizations/explore/_index.md",
    # Administration
    "docs/sources/administration/_index.md",
    "docs/sources/administration/user-management/_index.md",
    "docs/sources/administration/roles-and-permissions/_index.md",
    "docs/sources/administration/provisioning/_index.md",
    "docs/sources/administration/plugin-management/_index.md",
    # Setup
    "docs/sources/setup-grafana/_index.md",
    "docs/sources/setup-grafana/installation/_index.md",
    "docs/sources/setup-grafana/configure-grafana/_index.md",
    "docs/sources/setup-grafana/configure-security/_index.md",
    "docs/sources/setup-grafana/configure-docker.md",
    "docs/sources/setup-grafana/sign-in-to-grafana.md",
    "docs/sources/setup-grafana/set-up-grafana-monitoring.md",
    # Tutorials
    "docs/sources/tutorials/_index.md",
    # Troubleshooting
    "docs/sources/troubleshooting/_index.md",
    # What's new (pick a few recent ones)
    "docs/sources/whatsnew/_index.md",
    "docs/sources/whatsnew/whats-new-in-v10-3.md",
    # Top-level index
    "docs/sources/_index.md",
]

BASE_URL = "https://raw.githubusercontent.com/grafana/grafana/main/"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "docs")


def _safe_filename(path: str) -> str:
    """Convert a repo path to a flat filename."""
    # strip leading docs/sources/
    name = path.replace("docs/sources/", "")
    # replace path separators with __
    name = name.replace("/", "__")
    # _index.md -> index.md
    return name


def download() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    success, failed = 0, []

    for path in DOCS:
        url = BASE_URL + path
        filename = _safe_filename(path)
        out_path = os.path.join(OUT_DIR, filename)

        try:
            urllib.request.urlretrieve(url, out_path)
            with open(out_path, "r", encoding="utf-8") as f:
                content = f.read(200)
            if "404: Not Found" in content or len(content) < 30:
                os.remove(out_path)
                failed.append(path)
                print(f"  SKIP (empty/404): {path}")
            else:
                success += 1
                print(f"  OK: {filename}")
        except Exception as e:
            failed.append(path)
            print(f"  FAIL: {path} — {e}")

    print(f"\nDownloaded {success} files. Failed: {len(failed)}.")
    if failed:
        print("Failed paths:")
        for p in failed:
            print(f"  {p}")


if __name__ == "__main__":
    download()
