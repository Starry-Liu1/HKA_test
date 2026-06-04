"""State and output schema."""

from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph.message import add_messages


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
    article_zh: str


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
    retriever: Any

    # Knowledge Computing
    figure_id: int
    figures: List[Dict[str, str]]
    used_tables: List[str]

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
    search_query: str
    url_cache: Dict[str, str]
    log_file: str

    # Intermediate
    search_intent: str
    search_results: List[Dict[str, str]]

    # Output
    relevant_information: str


class WsInputState(TypedDict):
    """Web Search Input State."""
    search_query: str
    url_cache: Dict[str, str]
    log_file: str


class WsOutputState(TypedDict):
    """Web Search Output State."""
    relevant_information: str
