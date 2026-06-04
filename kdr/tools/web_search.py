"""Web Search Agent."""

import re
from functools import partial
from typing import Annotated, Dict, List

from langchain_core.messages import (HumanMessage, SystemMessage,
                                     ToolMessage, get_buffer_string)
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from kdr.config import WEB_SEARCH_TOP_K
from kdr.model import get_writer_model
from kdr.prompts import FIND_RELEVANT_INFORMATION_PROMPT, SEARCH_INTENT_PROMPT
from kdr.state import KdrState, WsInputState, WsOutputState, WsState
from kdr.utils import (BM25Retriever, extract_context_by_snippet,
                       fetch_content_async, format_search_results, get_logger,
                       search_web)


@tool
async def web_search(
    search_query: Annotated[str, ..., "the query to search on the web."],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Web search tool that searches the webpages for a given query."""
    num_tool_calls = state.get("num_tool_calls", 0)
    url_cache = state.get("url_cache", {})
    retriever = state.get("retriever", BM25Retriever())
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.web_search", log_file)
    logger.info("=== Web Search ===")

    agent = web_search_agent()

    response = await agent.ainvoke(
        {
            "search_query": search_query,
            "url_cache": url_cache,
            "log_file": log_file,
            # Initialize intermediate fields
            "search_intent": "",
            "search_results": [],
            "relevant_information": "",
        },
    )

    relevant_information = response.get("relevant_information", "")
    url_cache = response.get("url_cache", url_cache)
    retriever = response.get("retriever", retriever)

    logger.info(
        "Relevant Information:\n"
        "%s\n",
        relevant_information,
    )

    return Command(
        update={
            "url_cache": url_cache,
            "retriever": retriever,
            "num_tool_calls": num_tool_calls + 1,
            "history": [ToolMessage(relevant_information, tool_call_id=tool_call_id)],
        }
    )


def web_search_agent():
    """Web search agent."""
    builder = StateGraph(
        WsState,
        input_schema=WsInputState,
        output_schema=WsOutputState,
    )

    builder.add_node("generate_search_intent", generate_search_intent)
    builder.add_node("search_webpages", search_webpages)
    builder.add_node("extract_relevant_information", extract_relevant_information)

    builder.add_edge(START, "generate_search_intent")
    builder.add_edge("generate_search_intent", "search_webpages")
    builder.add_edge("search_webpages", "extract_relevant_information")
    builder.add_edge("extract_relevant_information", END)

    return builder.compile()


def generate_search_intent(
    state: WsState,
    prompt: str = SEARCH_INTENT_PROMPT,
):
    """Generate search intent."""
    search_query = state.get("search_query", "")
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.web_search", log_file)

    model = get_writer_model()

    content = prompt.format(
        question=search_query,
        current_subtask=search_query,
        search_query=search_query,
        history="",
    )
    response = model.invoke([SystemMessage(content)])
    search_intent = response.content

    logger.info("Search Intent:\n%s\n", search_intent)

    return {
        "search_intent": search_intent,
    }


def is_valid_content(content: str, max_links: int = 100) -> bool:
    """Check if the content is valid for processing.

    Args:
        content: The content to check
        max_links: Maximum number of links allowed (default: 100)

    Returns:
        True if content is valid, False otherwise
    """
    # Check for empty or invalid content messages
    invalid_patterns = [
        "please enable cookies",
        "please enable javascript",
        "enable cookies",
        "enable javascript",
        "javascript is required",
        "cookies are required",
        "access denied",
        "page not found",
        "404 not found",
        "can not fetch the page content",
        "正在验证您是否是真人"
    ]

    content_lower = content.lower().strip()
    for pattern in invalid_patterns:
        if pattern in content_lower:
            return False

    # Check if content is too short (less than 50 characters)
    if len(content.strip()) < 50:
        return False

    # Count hyperlinks using markdown format [text](url) and HTML <a> tags
    markdown_links = len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content))
    html_links = len(re.findall(r'<a\s+[^>]*href[^>]*>', content, re.IGNORECASE))
    total_links = markdown_links + html_links

    if total_links > max_links:
        return False

    return True


def clean_content(content: str) -> str:
    """
    Clean and normalize web page content for better extraction.

    This function removes noise, irrelevant elements, and normalizes the text
    to improve the quality of data extraction.

    Args:
        content: Raw web page content

    Returns:
        Cleaned and normalized content
    """
    if not content:
        return content

    # Remove HTML script tags and their content
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML style tags and their content
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Remove common navigation and footer patterns
    nav_patterns = [
        r'navigation.*?Skip to content',
        r'Skip to navigation.*?main content',
        r'Menu.*?Close',
        r'Copyright.*?\d{4}.*?All rights reserved',
        r'Privacy Policy.*?Terms of Use',
        r'Cookie Policy.*?Accept',
        r'Subscribe.*?newsletter',
        r'Follow us on.*?social media',
    ]
    for pattern in nav_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)

    # Remove excessive whitespace (more than 2 consecutive newlines)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

    # Remove excessive spaces within lines
    content = re.sub(r' {2,}', ' ', content)

    # Remove common control characters
    content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)

    # Normalize different types of dashes and quotes
    content = content.replace('–', '-')  # en-dash to hyphen
    content = content.replace('—', '--')  # em-dash to two hyphens
    content = content.replace('“', '"')
    content = content.replace('”', '"')
    content = content.replace('‘', "'")
    content = content.replace('’', "'")

    # Remove URL parameters from common tracking patterns
    content = re.sub(r'\?utm_[^&\s]+&?[^"\']*', '', content)
    content = re.sub(r'&utm_[^&\s]+', '', content)

    # Remove or replace common meaningless phrases
    useless_phrases = [
        r'click here for more information',
        r'please enable javascript',
        r'cookies are used',
        r'by continuing to use this site',
        r'this website uses cookies',
        r'all rights reserved',
    ]
    for phrase in useless_phrases:
        content = re.sub(phrase, '', content, flags=re.IGNORECASE)

    # Clean up any resulting empty lines or extra spaces
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)

    # Ensure proper spacing around punctuation
    content = re.sub(r'\s+([,.!?;:])', r'\1', content)  # Space before punctuation
    content = re.sub(r'([,.!?;:])(?![\s\d])', r'\1 ', content)  # Space after punctuation (if not number)

    # Remove repeated punctuation marks
    content = re.sub(r'([.!?]){4,}', r'\1\1\1', content)  # Limit to 3

    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # Strip leading/trailing whitespace
    content = content.strip()

    return content


async def search_webpages(
    state: WsState,
    web_search_top_k: int = 10,
):
    """Search webpages (async version to avoid blocking calls)."""
    search_query = state.get("search_query", "")
    url_cache = state.get("url_cache", {})
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.web_search", log_file)

    results = search_web(
        query=search_query,
        max_results=web_search_top_k
    )
    url_to_fetch = []
    for result in results:
        if result["url"] not in url_cache:
            url_to_fetch.append(result["url"])

    for url in url_to_fetch:
        content = await fetch_content_async(url)
        url_cache.setdefault(url, content)

    valid_results = []
    for i, result in enumerate(results):
        raw_content = url_cache[result["url"]]
        if i < 5:
            context_chars = 12000
        else:
            context_chars = 10000
        if raw_content != "Can not fetch the page content.":
            context = extract_context_by_snippet(
                raw_content=raw_content,
                snippet=result["snippet"],
                context_chars=context_chars,
            )
            context = clean_content(context)
            result["content"] = context
            valid_results.append(result)

    logger.info("Fetched Webpages: %d\n", len(valid_results))

    return {
        "url_cache": url_cache,
        "search_results": valid_results,
    }


def extract_relevant_information(
    state: WsState,
    prompt: str = FIND_RELEVANT_INFORMATION_PROMPT,
):
    """Extract relevant information."""
    search_query = state.get("search_query", "")
    search_intent = state.get("search_intent", "")
    search_results = state.get("search_results", [])
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.web_search", log_file)

    model = get_writer_model()
    formatted_results = format_search_results(search_results)

    content = prompt.format(
        search_query=search_query,
        search_intent=search_intent,
        search_result=formatted_results,
    )

    response = model.invoke([SystemMessage(content)])
    relevant_information = response.content

    logger.info("Relevant Information:\n%s\n", relevant_information)

    return {
        "relevant_information": relevant_information,
    }
