"""Run KDR from the command line."""

import argparse
import asyncio
import json
import logging
import os
import uuid
from pathlib import Path

import nltk

from kdr.graph import knowledgeable_deep_research


DEFAULT_REPORT_ID_DICT_PATH = Path("./report_id_dict.json")
DEFAULT_QUESTION_ITEMS = [
    {
        "key": "european_banking_competition",
        "question": (
            "Considering ongoing industry consolidation and the varied pace of AI "
            "adoption, how might the competitive landscape of European banking "
            "evolve, especially regarding the distribution of corporate and retail "
            "lending between traditional universal banks and newer digital banking "
            "entities?"
        ),
    }
]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the HKA/KDR workflow.")
    parser.add_argument(
        "-q",
        "--question",
        help="Single research question to run.",
    )
    parser.add_argument(
        "--key",
        help="Optional key for --question in report_id_dict.json.",
    )
    parser.add_argument(
        "--questions-file",
        type=Path,
        help=(
            "JSON file containing a list of questions or objects with "
            "`question` and optional `key` fields."
        ),
    )
    parser.add_argument(
        "--output-root",
        default="static",
        help="Directory where report output folders are created.",
    )
    parser.add_argument(
        "--base-url",
        default="./",
        help="Base URL or path prefix used when formatting generated figures.",
    )
    parser.add_argument(
        "--report-id-dict",
        type=Path,
        default=DEFAULT_REPORT_ID_DICT_PATH,
        help="Path to the question-to-report-id mapping JSON file.",
    )
    parser.add_argument(
        "--recursion-limit",
        type=int,
        default=250,
        help="LangGraph recursion limit.",
    )
    parser.add_argument(
        "--nltk-data",
        default="./nltk_data",
        help="Local NLTK data directory.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Console logging level.",
    )
    return parser.parse_args()


def normalize_question_items(raw_items) -> list[dict[str, str]]:
    """Normalize supported question JSON formats."""
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("questions", [raw_items])

    if not isinstance(raw_items, list):
        raise ValueError("Questions file must contain a list or a {'questions': [...]} object.")

    items = []
    for i, item in enumerate(raw_items):
        if isinstance(item, str):
            question = item
            key = f"question_{i + 1}"
        elif isinstance(item, dict):
            question = item.get("question", "")
            key = item.get("key") or f"question_{i + 1}"
        else:
            raise ValueError("Each question item must be a string or an object.")

        question = question.strip()
        if not question:
            raise ValueError(f"Question item {i + 1} is empty.")
        items.append({"key": key, "question": question})
    return items


def load_question_items(args: argparse.Namespace) -> list[dict[str, str]]:
    """Load questions from CLI arguments."""
    if args.question:
        return [{
            "key": args.key or "cli_question",
            "question": args.question,
        }]

    if args.questions_file:
        with open(args.questions_file, "r", encoding="utf-8") as f:
            return normalize_question_items(json.load(f))

    return DEFAULT_QUESTION_ITEMS


async def run_question(
    question: str,
    output_root: str,
    base_url: str,
    recursion_limit: int,
) -> str:
    """Run a single question asynchronously and return its report id."""
    report_id = uuid.uuid4().hex[:6]
    output_dir = os.path.join(output_root, report_id)
    os.makedirs(output_dir, exist_ok=True)

    builder = knowledgeable_deep_research()
    agent = builder.compile()
    await agent.ainvoke(
        {
            "research_question": question,
            "output_dir": output_dir,
            "base_url": base_url,
            "log_file": os.path.join(output_dir, "kdr.log"),
            "figure_id": 0,
            "figures": [],
            "used_tables": [],
            "url_cache": {},
            "num_tool_calls": 0,
            "article": "",
            "executed_subtasks": [],
        },
        {
            "recursion_limit": recursion_limit,
            "configurable": {"thread_id": report_id},
        },
    )
    return report_id


def load_report_id_dict(path: Path) -> dict:
    """Load the existing question-to-report-id mapping."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_report_id_dict(path: Path, report_id_dict: dict) -> None:
    """Save the question-to-report-id mapping."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_id_dict, f, ensure_ascii=False, indent=2)


async def run_all(args: argparse.Namespace) -> None:
    """Run all configured questions."""
    report_id_dict = load_report_id_dict(args.report_id_dict)
    question_items = load_question_items(args)

    for item in question_items:
        try:
            report_id = await run_question(
                question=item["question"],
                output_root=args.output_root,
                base_url=args.base_url,
                recursion_limit=args.recursion_limit,
            )
        except Exception:
            logging.exception("Error occurred for question: %s", item["question"])
            continue

        report_id_dict[item["key"]] = report_id
        save_report_id_dict(args.report_id_dict, report_id_dict)
        logging.info("Saved report id for %s: %s", item["key"], report_id)


def main() -> None:
    """CLI entry point for KDR."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    nltk.data.path.append(args.nltk_data)
    asyncio.run(run_all(args))


if __name__ == "__main__":
    main()
