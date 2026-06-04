"""Subtask complete tool."""

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from kdr.utils import get_logger


@tool
def subtask_complete(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """Subtask complete."""
    log_file = state.get("log_file", None)
    num_tool_calls = state.get("num_tool_calls", 0)
    logger = get_logger("kdr.subtask_complete", log_file)
    logger.info(
        "=== Subtask Complete ===\n"
    )
    return Command(update={
        "complete_subtask_flag": True,
        "num_tool_calls": num_tool_calls + 1,
        "history": [ToolMessage("Subtask complete.", tool_call_id=tool_call_id)],
    })
