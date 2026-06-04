"""Preparation for kdr running."""

import json
import os

import nltk
from langchain_community.vectorstores import FAISS
from langchain_core.documents.base import Document

from kdr.config import (INSTANCE_FILE_PATH, INSTANCE_INDEX_PATH,
                        NLTK_DATA_PATH)
from kdr.model import QwenEmbedding


def main():
    """Prepare."""
    # Prepare nltk data
    nltk.download("punkt_tab", download_dir=NLTK_DATA_PATH)

    # Prepare Crawl4AI
  #  os.system("crawl4ai-setup")
  #  os.system("crawl4ai-doctor")


    # Prepare instance index
    if not os.path.exists(INSTANCE_INDEX_PATH):
        with open(INSTANCE_FILE_PATH, "r", encoding="utf-8") as f:
            instances = json.load(f)
        docs = [
            Document(
                page_content=instance["table_title"],
                metadata={
                    #"table_id": instance["table_id"],
                    "table_title": instance["table_title"],
                    "description": instance["description"],
                },
            )
            for instance in instances
        ]
        vectorstore = FAISS.from_documents(docs, embedding=QwenEmbedding())
        vectorstore.save_local(INSTANCE_INDEX_PATH)


if __name__ == "__main__":
    main()
