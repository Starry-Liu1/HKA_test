"""State and output schema."""

from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph.message import add_messages


def merge_dicts(left: Dict[str, str] | None, right: Dict[str, str] | None) -> Dict[str, str]:
    """Merge dictionary state updates from concurrent tool calls."""
    merged = {}
    if left:
        merged.update(left)
    if right:
        merged.update(right)
    return merged


def add_ints(left: int | None, right: int | None) -> int:
    """Add integer increments from concurrent tool calls."""
    return (left or 0) + (right or 0)


def merge_unique_strings(left: List[str] | None, right: List[str] | None) -> List[str]:
    """Merge lists while preserving first-seen order."""
    merged = []
    for value in (left or []) + (right or []):
        if value not in merged:
            merged.append(value)
    return merged


def merge_figures(
    left: List[Dict[str, str]] | None,
    right: List[Dict[str, str]] | None,
) -> List[Dict[str, str]]:
    """Merge generated figure records from concurrent tool calls."""
    return (left or []) + (right or [])


def merge_retrievers(left: Any, right: Any) -> Any:
    """Merge BM25Retriever-like objects produced by concurrent web searches."""
    if left is None:
        return right
    if right is None or left is right:
        return left

    right_docs = getattr(right, "docs", None)
    if hasattr(left, "add_documents") and isinstance(right_docs, list):
        left_docs = getattr(left, "docs", [])
        new_docs = [doc for doc in right_docs if doc not in left_docs]
        if new_docs:
            left.add_documents(new_docs)
        return left

    return right


#######
# State
#######
class KdrInputState(TypedDict):
    """KDR Input State."""
    research_question: str
    output_dir: str
    base_url: str
    log_file: str


class KdrOutputState(TypedDict):
    """KDR Output State."""


class KdrState(TypedDict):
    """KDR State."""
    # Input
    research_question: str
    output_dir: str
    base_url: str
    log_file: str

    # Output

    section_outline: str
    article: str

    # History
    # LangGraph message buffer. It can accumulate System/Tool/AI/Human
    # messages across turns and can also be cleared inside the graph.
    history: Annotated[list, add_messages]

    # Subtask supervisor
    subtasks: List[str]  # Subtasks decomposed by the model
    executed_subtasks: List[str]  # Completed subtasks
    current_subtask: str  # Current subtask being executed
    complete_subtask_flag: bool  # Whether the subtask is complete

    # Web Search
    retriever: Annotated[Any, merge_retrievers]
    url_cache: Annotated[Dict[str, str], merge_dicts]
    num_tool_calls: Annotated[int, add_ints]

    # Knowledge Computing
    figure_id: Annotated[int, add_ints]
    figures: Annotated[List[Dict[str, str]], merge_figures]
    used_tables: Annotated[List[str], merge_unique_strings]

class KcState(TypedDict):
    """Knowledge Computing State."""
    # Input
    question: str
    output_dir: str
    figure_id: int
    log_file: str
    used_tables: List[str]

    # Code
    concepts_code: str
    instances_code: str
    assertion_code: str
    computing_code: str

    # Entities
    entities: List[Dict[str, str]]

    # Output
    result: Dict[str, str]
    table_info: List[Dict[str, str]]

    # Feedback from validity judgment
    feedback: str  # Feedback from the judge_validity step to guide code regeneration
    validity_invalid_count: int  # Consecutive invalid figure judgments for current figure

class KcInputState(TypedDict):
    """Knowledge Computing Input State."""
    question: str
    output_dir: str
    figure_id: int
    log_file: str
    used_tables: List[str]
    feedback: str  # Feedback from previous judgment attempts (can be empty initially)
    validity_invalid_count: int  # Consecutive invalid figure judgments for current figure


class KcOutputState(TypedDict):
    """Knowledge Computing Output State."""
    result: Dict[str, str]
    table_info: List[Dict[str, str]]
    feedback: str  # Feedback from validity judgment
    validity_invalid_count: int  # Consecutive invalid figure judgments for current figure


###################
# Structured Output
###################
class ResearchSubtasks(TypedDict):
    """Subtasks for the research task."""

    subtasks: Annotated[List[str], ..., "List of subtasks to complete the research task."]


class Entity(TypedDict):
    """Entity extracted from the text."""

    name: Annotated[str, ..., "The entity's name found in the text."]
    type: Annotated[str, ..., "The type of the entity (e.g., person, organization)."]
    description: Annotated[str, ..., "A brief description of the entity."]


class ExtractionResults(TypedDict):
    """Extraction results."""

    entities: Annotated[List[Entity], ..., "List of entities extracted from the text."]


class WsState(TypedDict):
    """Web Search State."""
    # Input
    research_question: str
    current_subtask: str
    search_query: str
    history: list
    url_cache: Dict[str, str]
    log_file: str

    # Intermediate
    search_intent: str
    search_results: List[Dict[str, str]]

    # Output
    relevant_information: str


class WsInputState(TypedDict):
    """Web Search Input State."""
    research_question: str
    current_subtask: str
    search_query: str
    history: list
    url_cache: Dict[str, str]
    log_file: str


class WsOutputState(TypedDict):
    """Web Search Output State."""
    relevant_information: str
    url_cache: Dict[str, str]
    search_results: List[Dict[str, str]]
