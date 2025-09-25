"""Command-line entry point for the greenwashing pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the src directory is importable when running the script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from greenwashing_pipeline.pipeline import GreenwashingPipeline
from greenwashing_pipeline.llm_evaluator import ConsistencyEvaluator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the greenwashing detection pipeline.")
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a PDF file or a directory containing PDF files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "pipeline_output.json",
        help="Where to store the JSON result (default: pipeline_output.json in the project root).",
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Do not call the DeepSeek model; only extract claims and KPIs.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit the number of pages processed per document.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evaluator = None if args.skip_evaluation else ConsistencyEvaluator()
    pipeline = GreenwashingPipeline(evaluator=evaluator, max_pages=args.max_pages)

    if args.input.is_dir():
        outputs = pipeline.process_directory(args.input, evaluate=not args.skip_evaluation)
    else:
        outputs = [pipeline.process(args.input, evaluate=not args.skip_evaluation)]

    payload = [output.to_dict() for output in outputs]
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Saved {len(payload)} pipeline results to {args.output}")


if __name__ == "__main__":
    main()

