"""Utility functions."""

import asyncio
import json
import os
import logging
import string
from typing import Dict, List, Set

# Fix fake_useragent issue by setting fallback before importing
os.environ['FAKE_USERAGENT_FALLBACK'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

import nltk
import numpy as np
from crawl4ai import AsyncWebCrawler, BrowserConfig
from langchain_community.utilities import GoogleSerperAPIWrapper
from mrkdwn_analysis import MarkdownAnalyzer
from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Okapi

# Configure NLTK data path to use project-local nltk_data directory
# Set the path to the project's nltk_data directory
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_nltk_data_path = os.path.join(_project_root, 'nltk_data')

# Add to NLTK search paths if it exists
if os.path.exists(_nltk_data_path):
    nltk.data.path.append(_nltk_data_path)
else:
    # Fallback to environment variable or default paths
    nltk_data_path = os.environ.get('NLTK_DATA', '')
    if nltk_data_path and os.path.exists(nltk_data_path):
        nltk.data.path.append(nltk_data_path)


def get_logger(
    name: str,
    log_file: str = None,
) -> logging.Logger:
    """Get logger."""
    logger = logging.getLogger(name)
    if (log_file is not None) and (not logger.handlers):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        logger.addHandler(file_handler)
    return logger


def extract_outline(content: str) -> str:
    """Extract the outline of a markdown article."""
    analyzer = MarkdownAnalyzer.from_string(content)
    results = analyzer.identify_headers()
    outline = ""
    for header in results.get("Header", []):
        outline += f"{'#' * header['level']} {header['text']}\n"
    return outline


def search_google_serper(
    query: str,
    max_results: int
) -> List[Dict[str, str]]:
    """Search query from google."""
    # Search results
    search = GoogleSerperAPIWrapper(
        type="search",  # organic
        k=max_results,
        #type="",  # scholarly
    )
    results = search.results(query)

    # Convert results
    if "organic" in results:
        search_results = [
            {
                "id": result["position"],
                "title": result["title"],
                "url": result["link"],
                "snippet": result["snippet"],
                "content": ""
            }
            for result in results["organic"]
        ]
    else:
        search_results = []
    return search_results


def fetch_content(url: str) -> str:
    """Fetch webpage content (synchronous wrapper for backward compatibility)."""
    async def fetch_content_async(url: str) -> str:
        """Async function to fetch webpage content."""
        # Configure browser to avoid fake_useragent issues
        browser_config = BrowserConfig(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            verbose=False,
        )

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url)
            if result.success and result.markdown.strip():
                md_content = result.markdown.strip()
            else:
                md_content = "Can not fetch the page content."
        except Exception as e:
            # Fallback if crawler fails
            logging.warning(f"Failed to fetch {url} with AsyncWebCrawler: {e}")
            md_content = "Can not fetch the page content."

        return md_content

    return asyncio.run(fetch_content_async(url))


async def fetch_content_async(url: str) -> str:
    """Fetch webpage content (async version for LangGraph nodes).

    This async version should be used in LangGraph nodes to avoid blocking calls.
    """
    # Configure browser to avoid fake_useragent issues
    browser_config = BrowserConfig(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
        verbose=False,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url)
        if result.success and result.markdown.strip():
            md_content = result.markdown.strip()
        else:
            md_content = "Can not fetch the page content."
    except Exception as e:
        # Fallback if crawler fails
        logging.warning(f"Failed to fetch {url} with AsyncWebCrawler: {e}")
        md_content = "Can not fetch the page content."

    return md_content


def bag_of_words(sent: str) -> Set[str]:
    """Convert a sentence into a bag of words."""
    # Remove punctuation in sentence
    sent = sent.translate(str.maketrans("", "", string.punctuation))
    return set(sent.lower().split())


def f1_score(true_set: Set[str], pred_set: Set[str]) -> float:
    """Compute F1 score of two sets."""
    intersection = true_set.intersection(pred_set)
    if intersection:
        p = len(intersection) / len(pred_set)
        r = len(intersection) / len(true_set)
        return 2 * p * r / (p + r)
    return 0.


def extract_context_by_snippet(
    raw_content: str,
    snippet: str,
    context_chars: int = 4000,
) -> str:
    """Extract the context from document via snippet."""
    # Split sentences
    sents = nltk.sent_tokenize(raw_content)
    snippet_words = bag_of_words(snippet)

    # Main idea is to find the most relevant sentence and expand the context
    best_f1 = 0.2
    best_sent_id = -1
    for i, sent in enumerate(sents):
        sent = sent.translate(str.maketrans("", "", string.punctuation))
        sent_words = bag_of_words(sent)
        f1 = f1_score(snippet_words, sent_words)
        if f1 > best_f1:
            best_f1, best_sent_id = f1, i
    if best_sent_id >= 0:
        key_sent = sents[best_sent_id]
        sent_start = raw_content.find(key_sent)
        start_idx = max(0, sent_start - context_chars)
        return raw_content[start_idx:start_idx + len(key_sent) + context_chars]

    return raw_content[:2 * context_chars]


def format_search_results(
    search_results: List[Dict[str, str]],
    with_content: bool = True,
) -> str:
    """Format search results into readable string."""
    formatted_results = ""
    for i, result in enumerate(search_results):
        formatted_results += f"***Web Page {i+1}:***\n"
        page_info = {
            "title": result["title"],
            "url": result["url"],
            "snippet": result["snippet"],
        }
        if with_content:
            page_info["content"] = result["content"]
        formatted_results += json.dumps(page_info, indent=2, ensure_ascii=False)
        formatted_results += "\n"

    return formatted_results


def format_computing_result(
    result: Dict[str, str],
    base_url: str = "http://127.0.0.1:8000",
) -> str:
    """Format analysis result into readable string."""
    if not result.get("name", ""):
        return None

    # Generate content
    if base_url:
        path = f"{base_url}/{result['path']}"
    else:
        path = result["path"]
    content = f"![{result['name']}]({path})"
    return json.dumps({
        "name": result["name"],
        "content": content,
        "analysis": result["desc"],
    })


class BM25Retriever:
    """Modify BM25Retriever to support add_documents."""

    def __init__(self):
        self.docs = []
        self.tokenized_docs = []
        self.bm25 = None

    def add_documents(self, docs: List[str]):
        """Add new documents to the retriever."""
        # rank_bm25 does not support incremental updates, so we need to build all indices
        self.docs.extend(docs)
        self.tokenized_docs.extend([word_tokenize(doc.lower()) for doc in docs])
        if self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)
        else:
            self.bm25 = None

    def invoke(self, query: str, k: int = 3) -> List[str]:
        """Retrieve top k documents for a given query."""
        if self.bm25 is None:
            return []

        tokenized_query = word_tokenize(query.lower())
        doc_scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(doc_scores)[-k:][::-1]
        return [self.docs[i] for i in top_indices]
