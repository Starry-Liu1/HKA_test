"""Graph."""

import os
from typing import Literal

from langchain_core.messages import RemoveMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from kdr.config import MAX_OUTPUT_RETRY, TOTAL_TOOL_CALL
from kdr.model import get_planner_model, get_writer_model
from kdr.prompts import (FINAL_REFINEMENT_PROMPT, FINAL_POLISH_PROMPT, GENERATE_PLAN_PROMPT, FINAL_TRANSLATION_PROMPT,
                         SUPERVISOR_PROMPT, WRITE_SECTION_PROMPT,
                         WRITE_SECTION_OUTLINE_PROMPT)
from kdr.state import KdrInputState, KdrOutputState, KdrState, ResearchSubtasks
from kdr.tools.knowledge_computing import knowledge_computing
from kdr.tools.subtask_complete import subtask_complete
from kdr.tools.web_search import web_search
from kdr.utils import (BM25Retriever, extract_outline, format_computing_result,
                       get_logger)


def knowledgeable_deep_research():
    """Knowledgeable Deep Research agent."""
    tools = [web_search, knowledge_computing, subtask_complete]
    builder = StateGraph(
        KdrState,
        input_schema=KdrInputState,
        output_schema=KdrOutputState,
    )

    builder.add_node(
        "generate_subtask",
        generate_subtask,
    )
    builder.add_node(
        "execute_subtask",
        execute_subtask,
        destinations=("supervisor", "final_refinement"),
    )
    builder.add_node(
        "supervisor",
        supervisor,
        destinations=("supervisor_tool", "write_section_outline"),
    )
    builder.add_node(
        "supervisor_tool",
        ToolNode(
            tools,
            messages_key="history"
        ),
    )
    builder.add_node(
        "write_section_outline",
        write_section_outline,
    )
    builder.add_node(
        "write_section",
        write_section,
    )
    builder.add_node(
        "final_refinement",
        final_refinement,
    )
    builder.add_node(
        "final_polish",
        final_polish,
    )

    builder.add_edge(START, "generate_subtask")
    builder.add_edge("generate_subtask", "execute_subtask")
    builder.add_edge("supervisor_tool", "supervisor")
    builder.add_edge("write_section_outline", "write_section")
    builder.add_edge("write_section", "execute_subtask")
    builder.add_edge("final_refinement", "final_polish")
    builder.add_edge("final_polish", END)


    return builder


def generate_subtask(
    state: KdrState,
    prompt: str = GENERATE_PLAN_PROMPT,
):
    """Generate subtask."""
    research_question = state.get("research_question", "")
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.generate_subtask", log_file)
    logger.info("=== Generate Subtasks ===")

    model = get_writer_model()
    model_with_structure = model.with_structured_output(
        ResearchSubtasks,
        include_raw=True,
    ).with_retry(
        stop_after_attempt=MAX_OUTPUT_RETRY,
    )
    response = model_with_structure.invoke([
        SystemMessage(prompt.format(question=research_question)),
    ])

    subtasks = response["parsed"]["subtasks"]
    logger.info(
        "Subtasks:\n"
        "%s\n",
        "\n".join(subtasks)
    )

    return {
        "subtasks": subtasks,
    }


def execute_subtask(
    state: KdrState,
) -> Command[Literal["supervisor", "final_refinement"]]:
    """Execute subtask."""
    subtasks = state.get("subtasks", [])
    executed_subtasks = state.get("executed_subtasks", [])
    num_tool_calls = state.get("num_tool_calls", 0)
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.execute_subtask", log_file)
    logger.info("=== Execute Subtask ===")

    if (subtasks == executed_subtasks) or (num_tool_calls >= TOTAL_TOOL_CALL):
        logger.info(
            "All subtasks completed\n"
        )
        return Command(
            goto="final_refinement",
        )

    # Log output
    logger.info(
        "Current Subtask: %s\n",
        subtasks[len(executed_subtasks)],
    )

    return Command(
        goto="supervisor",
        update={
            "current_subtask": subtasks[len(executed_subtasks)],
            "complete_subtask_flag": False,
            "history": [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
        }
    )


def supervisor(
    state: KdrState,
    prompt: str = SUPERVISOR_PROMPT,
) -> Command[Literal["supervisor_tool", "write_section"]]:
    """Supervisor."""
    research_question = state.get("research_question", "")
    current_subtask = state.get("current_subtask", "")
    complete_subtask_flag = state.get("complete_subtask_flag", False)
    history = state.get("history", [])
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.supervisor", log_file)
    logger.info("=== Supervisor ===")

    if complete_subtask_flag:
        return Command(goto="write_section_outline")

    if not history:
        init_content = prompt.format(
            question=research_question,
            current_subtask=current_subtask,
        )
        history.append(SystemMessage(init_content))
    else:
        history.append(SystemMessage("Please generate next tool call."))

    model = get_planner_model()
    tools = [web_search, knowledge_computing, subtask_complete]
    model_with_tool = model.bind_tools(tools).with_retry(
        stop_after_attempt=MAX_OUTPUT_RETRY,
    )
    response = model_with_tool.invoke(history)
    logger.info(
        "Tool calls:\n"
        "%s\n",
        "\n".join([
            f"Name: {call['name']}, Args: {call['args']}"
            for call in response.tool_calls
        ])
    )

    if not response.tool_calls:
        return Command(goto="write_section_outline")

    return Command(
        goto="supervisor_tool",
        update={
            "history": history + [response],
        }
    )

def write_section_outline(
    state: KdrState,
    prompt: str = WRITE_SECTION_OUTLINE_PROMPT,
):
    """Write section outline."""
    research_question = state.get("research_question_en", "")
    history = state.get("history", [])
    current_subtask = state.get("current_subtask", "")
    figure_id = state.get("figure_id", 0)
    figures = state.get("figures", [])
    base_url = state.get("base_url", "")
    retriever = state.get("retriever", BM25Retriever())
    article = state.get("article", "")
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.write_section", log_file)
    logger.info("=== Write Section Outline ===")

    relevant_documents = retriever.invoke(current_subtask)
    formatted_documents = ""
    for i, doc in enumerate(relevant_documents):
        formatted_documents += f"Document {i}:\n{doc}\n\n"

    formatted_figures = ""
    fig_id_offset = figure_id - len(figures)
    for i, fig in enumerate(figures):
        format_fig = format_computing_result(fig, base_url)
        formatted_figures += f"Figure {i + fig_id_offset}:\n{format_fig}\n\n"

    model = get_writer_model()
    article_outline = extract_outline(article)
    content = prompt.format(
        relevant_documents=formatted_documents,
        figures=formatted_figures,
        question=research_question,
        current_subtask=current_subtask,
        article_outline=article_outline,
    )
    response = model.invoke(history + [SystemMessage(content)])
    section_outline = response.content
    logger.info(f"section_outline: {section_outline}")

    return {
        "section_outline": section_outline
    }

def write_section(
    state: KdrState,
    prompt: str = WRITE_SECTION_PROMPT,
):
    """Write section."""
    research_question = state.get("research_question_en", "")
    history = state.get("history", [])
    current_subtask = state.get("current_subtask", "")
    executed_subtasks = state.get("executed_subtasks", [])
    section_outline = state.get("section_outline", "")
    figure_id = state.get("figure_id", 0)
    figures = state.get("figures", [])
    base_url = state.get("base_url", "")
    retriever = state.get("retriever", BM25Retriever())
    article = state.get("article", "")
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.write_section", log_file)
    logger.info("=== Write Section ===")

    relevant_documents = retriever.invoke(current_subtask)
    formatted_documents = ""
    for i, doc in enumerate(relevant_documents):
        formatted_documents += f"Document {i}:\n{doc}\n\n"

    formatted_figures = ""
    fig_id_offset = figure_id - len(figures)
    for i, fig in enumerate(figures):
        format_fig = format_computing_result(fig, base_url)
        formatted_figures += f"Figure {i + fig_id_offset}:\n{format_fig}\n\n"

    model = get_writer_model()
    article_outline = extract_outline(article)
    content = prompt.format(
        relevant_documents=formatted_documents,
        figures=formatted_figures,
        question=research_question,
        current_subtask=current_subtask,
        article_outline=article_outline,
        section_outline=section_outline,
    )
    response = model.invoke(history + [SystemMessage(content)])
    section_content = response.content
    logger.info(f"section_content: {section_content}")
    article += section_content

    executed_subtasks.append(current_subtask)
    return {
        "article": article,
        "history": history,
        "executed_subtasks": executed_subtasks,
    }


def final_refinement(
    state: KdrState,
    prompt: str = FINAL_REFINEMENT_PROMPT,
):
    """Final refinement."""
    research_question = state.get("research_question", "")
    output_dir = state.get("output_dir", "")
    article = state.get("article", "")
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.final_refinement", log_file)
    logger.info("=== Final Refinement ===")
    used_tables = state.get("used_tables", [])

    model = get_writer_model()
    content = prompt.format(
        question=research_question,
        article=article,
    )
    response = model.invoke([SystemMessage(content)])
    final_report = response.content

    with open(os.path.join(output_dir, "report_en.md"), "w", encoding="utf-8") as f:
        f.write(final_report)
    import json
    with open(os.path.join(output_dir, "used_tables.json"), "w", encoding="utf-8") as f:
        json.dump(used_tables, f, ensure_ascii=False, indent=4)

    logger.info(
        "Final report:\n"
        "%s\n",
        final_report,
    )

    return {
        "article": final_report,
    }


def final_polish(
    state: KdrState,
    prompt: str = FINAL_POLISH_PROMPT,
):
    """Final polish - second pass refinement for overall quality."""
    research_question = state.get("research_question", "")
    output_dir = state.get("output_dir", "")
    article = state.get("article", "")
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.final_polish", log_file)
    logger.info("=== Final Polish (Second Pass Refinement) ===")

    model = get_writer_model()
    content = prompt.format(
        question=research_question,
        article=article,
    )
    response = model.invoke([SystemMessage(content)])
    polished_report = response.content

    with open(os.path.join(output_dir, "report_en.md"), "w", encoding="utf-8") as f:
        f.write(polished_report)

    logger.info(
        "Polished report:\n"
        "%s\n",
        polished_report,
    )
    logger.info("Final polish completed successfully")

    return {
        "article": polished_report,
    }




graph = knowledgeable_deep_research().compile()
