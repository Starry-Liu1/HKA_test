"""Run KDR."""

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path

import nltk

from kdr.graph import knowledgeable_deep_research

REPORT_ID_DICT_PATH = Path(
    "/Users/liuwenxuan/kdr-web-demo-research-release/"
    "report_id_dict_w_cite_figure_comments_new.json"
)

QUESTION_ITEMS = [
    {
        "key": "Finance  Insurance_Financial Institutions_Banking_industry_in_Europe_Considering ongoing industry consolidation and the varied pace of AI adoption, how might the competitive landscape of European banking evolve, especially regarding the distribution of corporate and retail lending between traditional universal banks and newer digital banking entities?",
        "question": "Considering ongoing industry consolidation and the varied pace of AI adoption, how might the competitive landscape of European banking evolve, especially regarding the distribution of corporate and retail lending between traditional universal banks and newer digital banking entities?",
    }
]

async def run_question(question):
    """Run a single question asynchronously."""
    report_id = uuid.uuid4().hex[:6]
    output_dir = os.path.join("static", report_id)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    os.makedirs(output_dir, exist_ok=True)
    try:
        builder = knowledgeable_deep_research()
        agent = builder.compile()
        await agent.ainvoke(
            {
                "research_question": question,
                "output_dir": output_dir,
                "base_url": "./",
                "log_file": os.path.join(output_dir, "kdr.log"),
                # Initialize figure_id, figures, and used_tables to prevent them from resetting
                "figure_id": 0,
                "figures": [],
                "used_tables": [],
            },
            {
                "recursion_limit": 250,
                "configurable": {"thread_id": report_id}
            }
        )
        return report_id
    except Exception as e:
        print(e)
        print(f"Error occurred for question: {question}")
        return None


def load_report_id_dict():
    """Load the existing question-to-report-id mapping."""
    if not REPORT_ID_DICT_PATH.exists():
        return {}
    with open(REPORT_ID_DICT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_report_id_dict(report_id_dict):
    """Save the question-to-report-id mapping."""
    REPORT_ID_DICT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_ID_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_id_dict, f, ensure_ascii=False, indent=2)


def main():
    """Main entry point for KDR."""
    nltk.data.path.append("./nltk_data")

    report_id_dict = load_report_id_dict()
    for item in QUESTION_ITEMS:
        report_id = asyncio.run(run_question(item["question"]))
        if report_id is None:
            continue
        report_id_dict[item["key"]] = report_id
        save_report_id_dict(report_id_dict)
        print(f"Saved report id for question: {report_id}")


if __name__ == "__main__":
    main()
