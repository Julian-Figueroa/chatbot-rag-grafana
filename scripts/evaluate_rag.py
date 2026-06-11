"""
RAGAS evaluation for the Grafana RAG pipeline.

Usage:
    python scripts/evaluate_rag.py
    python scripts/evaluate_rag.py --output baseline
    python scripts/evaluate_rag.py --output chunk800 --dataset data/eval_dataset.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import AnswerRelevancy, Faithfulness, ContextPrecision, ContextRecall

from app.rag.pipeline import RAGPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the Grafana RAG pipeline with RAGAS")
    parser.add_argument(
        "--output",
        default=None,
        help="Label appended to the results CSV filename (e.g. 'baseline', 'chunk800')",
    )
    parser.add_argument(
        "--dataset",
        default="data/eval_dataset.json",
        help="Path to the evaluation dataset JSON file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"ERROR: Dataset not found at {dataset_path}")
        sys.exit(1)

    with open(dataset_path) as f:
        eval_data = json.load(f)

    print(f"Loaded {len(eval_data)} evaluation items from {dataset_path}")
    print("Initialising RAG pipeline...")
    pipeline = RAGPipeline()
    doc_count = pipeline.doc_count()
    print(f"  ChromaDB documents: {doc_count}")
    if doc_count == 0:
        print("WARNING: No documents in vectorstore. Run scripts/ingest_docs.py first.")

    print("\nRunning pipeline queries...")
    results = []
    errors = 0
    for i, item in enumerate(eval_data, start=1):
        q = item["question"]
        print(f"[{i:02d}/{len(eval_data)}] {q[:70]}{'...' if len(q) > 70 else ''}")
        try:
            response = pipeline.query(q, session_id=f"eval_{i}")
            results.append(
                {
                    "question": q,
                    "answer": response["answer"],
                    "contexts": response.get("retrieved_contexts", []),
                    "ground_truth": item["ground_truth"],
                }
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            errors += 1

    if not results:
        print("No results collected — cannot evaluate.")
        sys.exit(1)

    print(f"\n{len(results)} queries completed ({errors} errors). Running RAGAS evaluation...")

    # RAGAS 0.2.x expects a HuggingFace Dataset with these column names
    dataset = Dataset.from_list(results)

    score = evaluate(
        dataset,
        metrics=[
            Faithfulness(),
            AnswerRelevancy(),
            ContextPrecision(),
            ContextRecall(),
        ],
    )

    print("\n=== RAGAS Evaluation Results ===")
    print(score)

    # Save per-question breakdown to CSV for comparison across runs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = f"_{args.output}" if args.output else ""
    out_path = Path("data") / f"eval_results{label}_{timestamp}.csv"
    out_path.parent.mkdir(exist_ok=True)

    df = score.to_pandas()
    df.to_csv(out_path, index=False)
    print(f"\nPer-question scores saved to {out_path}")
    print("\nAggregate means:")
    numeric = df.select_dtypes("number")
    print(numeric.mean().to_string())


if __name__ == "__main__":
    main()
