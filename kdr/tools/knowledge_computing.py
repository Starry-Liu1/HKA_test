"""Knowledge computing."""

import base64
import json
import os
import re
import subprocess
import sys
import traceback
from functools import partial
from types import ModuleType
from typing import Annotated, Literal, Optional, Tuple
from langchain_core.documents.base import Document
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from kdr.config import (INSTANCE_INDEX_PATH,
                        INSTANCE_SCORE_THRESHOLD, INSTANCE_TOP_K, INSTANCE_SELECTION_K,
                        INSTANCE_FILE_PATH)
from kdr.model import (GenericEmbedding, get_analyzer_model, get_coder_model, get_writer_model)
from kdr.prompts import (CODE_FIX_PROMPT, CODE_GENERATION_PROMPT,
                         QUESTION_REWRITE_PROMPT,
                         RESULT_ANALYSIS_PROMPT, RESULT_NAME_PROMPT,
                         RESULT_VALIDITY_PROMPT, CODE_GENERATION_PROMPT_WHOLE_DATA,
                         RERANK_PROMPT)
from kdr.state import KcInputState, KcOutputState, KcState
from kdr.utils import format_computing_result, get_logger


def first_unused_table(table_infos: list[dict], used_tables: set[str]) -> dict:
    """Return the first table not already used."""
    for table_info in table_infos:
        if table_info.get("title") not in used_tables:
            return table_info
    return table_infos[0] if table_infos else {}


def load_instances_by_title() -> dict:
    """Load table metadata indexed by title."""
    with open(INSTANCE_FILE_PATH, "r", encoding="utf-8") as f:
        instances = json.load(f)
    return {
        instance["table_title"]: instance
        for instance in instances
        if instance.get("table_title")
    }


@tool
def knowledge_computing(
    question: Annotated[str, ..., "The research question to compute"],
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Knowledge computing tool that generates figures, tables and corresponding analysis."""
    output_dir = state.get("output_dir", "")
    base_url = state.get("base_url", "")
    figure_id = state.get("figure_id", 0)
    used_tables = state.get("used_tables", [])
    log_file = state.get("log_file", None)

    table_info = state.get("table_info", [])
    logger = get_logger("kdr.knowledge_computing", log_file)

    logger.info(f"Knowledge Computing with figure_id: {figure_id}")
    logger.info("=== Knowledge Computing ===")

    agent = knowledge_computing_agent()

    response = agent.invoke(
        {
            "question": question,
            "output_dir": output_dir,
            "figure_id": figure_id,
            "log_file": log_file,
            "used_tables": used_tables,
            "concepts_code": "",
            "instances_code": "",
            "assertion_code": "",
            "computing_code": "",
            "entities": [],
            "result": {},
            "table_info": table_info,
            "validity_invalid_count": 0,
        },
    )
    result = response.get("result", {})
    table_info = response.get("table_info", [])

    content = format_computing_result(result, base_url)
    new_figures = []
    figure_increment = 0
    if content is not None:
        figure_increment = 1
        new_figures.append(result)
    else:
        content = (
            "Fail to generate figure and analysis result. "
            "Try to modify the question, use other tools or complete this subtask.\n"
        )

    logger.info(
        "Figure:\n"
        "%s\n",
        content,
    )

    new_used_tables = used_tables.copy()

    for table in table_info:
        table_title = table.get("title", "")
        if table_title and table_title not in new_used_tables:
            new_used_tables.append(table_title)

    return Command(update={
        "figure_id": figure_increment,
        "history": [ToolMessage(content, tool_call_id=tool_call_id)],
        "used_tables": new_used_tables,
        "feedback":"",
        "num_tool_calls": 1,
        "figures": new_figures,
    })

def knowledge_computing_agent():
    """Knowledge computing agent."""
    builder = StateGraph(
        KcState,
        input_schema=KcInputState,
        output_schema=KcOutputState,
    )
    
    builder.add_node(
        "search_instances",
        partial(search_instances),
    )
    builder.add_node("rerank_tables", rerank_tables)
    builder.add_node("generate_computing_code", generate_computing_code)
    builder.add_node("execute_with_auto_repair", execute_with_auto_repair)
    builder.add_node(
        "judge_validity",
        judge_validity,
        destinations=("result_analysis", "generate_computing_code"),
    )
    builder.add_node("result_analysis", result_analysis)

    builder.add_edge(START, "search_instances")
    builder.add_edge("search_instances", "rerank_tables")
    builder.add_edge("rerank_tables", "generate_computing_code")
    builder.add_edge("generate_computing_code", "execute_with_auto_repair")
    builder.add_edge("execute_with_auto_repair", "judge_validity")
    builder.add_edge("result_analysis", END)
    return builder.compile()



def rerank_tables(
    state: KcState,
):
    """Rerank and select the most relevant tables using LLM."""
    question = state.get("question", "")
    table_info = state.get("table_info", [])
    log_file = state.get("log_file", None)

    top_k = INSTANCE_SELECTION_K

    logger = get_logger("kdr.knowledge_computing", log_file)

    if len(table_info) <= top_k:
        return {"table_info": table_info}

    table_summaries = []
    for i, table in enumerate(table_info):
        summary = f"""
Table {i}:
- Title: {table['title']}
- Content: {table['content'][:1000]}...
"""
        table_summaries.append(summary)

    summary_data = "".join(table_summaries)
    selection_prompt = RERANK_PROMPT.format(
        question=question,
        summary_data=summary_data,
        top_k=top_k
    )
    try:
        analyzer_model = get_writer_model()

        messages = [
            SystemMessage(content="You are an intelligent table selector that responds with valid JSON only."),
            HumanMessage(content=selection_prompt)
        ]

        response = analyzer_model.invoke(messages)
        response_text = response.content.strip()
        try:
            selection_data = json.loads(response_text)
            selected_indices = selection_data.get("selected_indices", [])

            valid_indices = []
            for idx in selected_indices:
                if 0 <= idx < len(table_info):
                    valid_indices.append(idx)

            valid_indices = list(dict.fromkeys(valid_indices))[:top_k]

            selected_tables = [table_info[i] for i in valid_indices]
            if selected_tables == []:
                selected_tables = table_info[:top_k]

            logger.info(f"LLM selected {len(selected_tables)} tables out of {len(table_info)}")

            return {"table_info": selected_tables}

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed, falling back to simple truncation: {e}")

    except Exception as e:
        logger.warning(f"Intelligent selection failed, falling back to simple truncation: {e}")

    return {"table_info": table_info[:top_k]}


def search_instances(
    state: KcState,
):
    """Search relevant table instances."""
    log_file = state.get("log_file", None)
    used_tables = state.get("used_tables", [])

    emb = GenericEmbedding()
    db = FAISS.load_local(
        INSTANCE_INDEX_PATH,
        embeddings=emb,
        allow_dangerous_deserialization=True,
    )
    retriever = db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": INSTANCE_TOP_K + len(used_tables),
            "score_threshold": INSTANCE_SCORE_THRESHOLD,
        }
    )

    question = state.get("question", "")
    logger = get_logger("kdr.knowledge_computing", log_file)
    instances_by_title = load_instances_by_title()

    instances = []
    entity_results_old = retriever.invoke(question)
    entity_results = []
    for result in entity_results_old:
        table_title = result.metadata.get('table_title', '')
        instance = instances_by_title.get(table_title)
        if not instance:
            continue
        doc = Document(
            page_content=table_title,
            metadata=instance,
        )
        entity_results.append(doc)
    for result in entity_results:
        table_title = result.metadata.get('table_title', '')
        table_name = result.metadata.get('table_name', '')
        if table_title in used_tables or table_name in used_tables:
            continue

        if result not in instances:
            instances.append(result)

    instances_code = "# Import necessary libraries for data handling\n"
    instances_code += "import matplotlib\n"
    instances_code += "matplotlib.use('Agg')  # Use non-interactive backend to prevent thread issues\n"
    instances_code += "import matplotlib.pyplot as plt\n"

    table_info = []

    for i, instance in enumerate(instances):
        table_name = instance.metadata.get("table_name", f"table_{i}")
        table_path = instance.metadata.get("file_path", "")
        table_title = instance.metadata.get("table_title", "")
        table_content = instance.metadata.get("table_data", "")
        table_data_model = instance.metadata.get("python_parsing_code", "Unknown")
        table_code_test_result = instance.metadata.get("code_test_result", "Unknown")
        output_data_comments = instance.metadata.get("output_data_comments", "")
        if table_title in used_tables:
            continue

        table_info.append({
            "name": table_name,
            "path": table_path,
            "title": table_title,
            "content": table_content,
            "table_data_model": table_data_model,
            "table_code_test_result": table_code_test_result,
            "output_data_comments": output_data_comments,
            "domain": instance.metadata.get("domain", "Unknown"),
            "sub_domain": instance.metadata.get("sub_domain", "Unknown"),
            "topic": instance.metadata.get("topic", "Unknown"),
        })

    assertion_code = ""
    for i, table_content1 in enumerate(table_info):
        instances_code += f"# Load table_data_{i} \n"
        instances_code += f"table_data_{i} = '''{table_content1['content']}'''\n"

    logger.info(
        "Searched table instances:\n"
        "%s\n",
        ", ".join([t["name"] for t in table_info])
    )

    return {
        "instances_code": instances_code,
        "assertion_code": assertion_code,
        "table_info": table_info,
    }


def generate_computing_code(
    state: KcState,
    prompt: str = CODE_GENERATION_PROMPT,
):
    """Generate code for the question based on table data."""
    question = state.get("question", "")
    output_dir = state.get("output_dir", "")
    figure_id = state.get("figure_id", 0)
    instances_code = state.get("instances_code", "")
    table_infos = state.get("table_info", [])
    if not isinstance(table_infos, list):
        table_infos = []

    used_tables = set(state.get("used_tables", []))
    table_info = first_unused_table(table_infos, used_tables)

    table_code_test_result = table_info.get("table_code_test_result", "Unknown")
    output_data_comments = table_info.get("output_data_comments", "")
    model = get_coder_model()
    figure_dir = os.path.join(output_dir, "figures")
    os.makedirs(figure_dir, exist_ok=True)

    if (
        isinstance(table_code_test_result, dict)
        and table_code_test_result.get("success") is True
    ):
        if output_data_comments:
            raw_output = table_code_test_result.get("output_data", {})
            if isinstance(raw_output, dict):
                sample_obj = {}
                for k, v in raw_output.items():
                    sample_obj[k] = v[:3] if isinstance(v, list) else v
            elif isinstance(raw_output, list):
                sample_obj = raw_output[:3]
            else:
                sample_obj = raw_output
            data_sample = json.dumps(sample_obj, indent=2)
        else:
            data_sample = ""
            
        custom_prompt = prompt.format(
            question=question,
            output_data_comments=output_data_comments,
            data_sample=data_sample,
            instance_code=instances_code,
            figure_dir=figure_dir,
            figure_id=figure_id,
        )    
        
    
    
    else:
        custom_prompt=CODE_GENERATION_PROMPT_WHOLE_DATA.format(
            question=question,
            instances_code=instances_code,
            figure_dir=figure_dir,
            figure_id=figure_id,
        )

    
    
    response = model.invoke([HumanMessage(content=custom_prompt)])
    computing_code = "# Computing code generated based on tables\n"
    
    code_blocks = re.findall(r"```python\n([\s\S]*?)\n```", response.content)
    if not code_blocks:
        code_blocks = [response.content]

    for code_block in code_blocks:
        computing_code += code_block + "\n"

    output_data = (
        table_code_test_result.get("output_data", {})
        if isinstance(table_code_test_result, dict)
        else {}
    )
    if "output_data_place_holder" in computing_code:
        computing_code = computing_code.replace(
            "output_data_place_holder",
            json.dumps(output_data, indent=2),
        )
    if "{{output_data}}" in computing_code:
        computing_code = computing_code.replace(
            "{{output_data}}",
            json.dumps(output_data, indent=2),
        )

    return {
        "computing_code": computing_code,
        "table_info": [table_info] if table_info else [],
    }


def execute_with_auto_repair(
    state: KcState,
):
    """Execute the generated code."""
    output_dir = state.get("output_dir", 0)
    figure_id = state.get("figure_id", 0)
    computing_code = state.get("computing_code", "")
    table_info = state.get("table_info", [])

    code_history = []
    attempt_num = 0
    max_attempts = 5
    output = None
    error = None
    while attempt_num < max_attempts:
        runnable_code = (
            f"{computing_code}\n"
        )

        code_file_path = os.path.join(output_dir, f"runnable_code_{figure_id}.py")
        with open(code_file_path, "w", encoding="utf-8") as f:
            f.write(runnable_code)

        _, output, error = execute_user_code(code_file_path)

        code_history.append({
            "code": runnable_code,
            "output": output,
            "error": error,
            "attempt_num": attempt_num,
        })

        if error and attempt_num < max_attempts - 1:
            computing_code = code_debug(code_history)
        else:
            break
        attempt_num += 1

    return {
        "result": output if not error else error,
        "table_info": table_info,
    }


def judge_validity(
    state: KcState,
    validity_prompt: str = RESULT_VALIDITY_PROMPT,
    rewrite_prompt: str = QUESTION_REWRITE_PROMPT,
) -> Command[Literal["result_analysis", "generate_computing_code"]]:
    """Judge validity."""

    question = state.get("question", "")
    figure_id = state.get("figure_id", 0)
    output_dir = state.get("output_dir", "")

    figure_path = os.path.join(output_dir, "figures", f"fig_{figure_id}.png")
    vl_model = get_analyzer_model()

    feedback = ""

    if os.path.exists(figure_path):
        with open(figure_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        text_content = validity_prompt.format(
            question=question,
        )

        content = [
            {
                "type": "text",
                "text": text_content
            },
            {
                "type": "image",
                "source_type": "base64",
                "data": image_data,
                "mime_type": "image/png",
            }
        ]
        try:
            response = vl_model.invoke([HumanMessage(content)])
            judge_result = str(response.content).strip()
        except Exception as e:
            feedback = f"Validity judge API failed or timed out: {type(e).__name__}: {e}"
            return Command(
                goto="result_analysis",
                update={
                    "feedback": feedback,
                }
            )
    else:
        judge_result = "False"
        feedback = "Figure file does not exist"
    if judge_result.lower().startswith("true"):
        return Command(
            goto="result_analysis",
            update={
                "validity_invalid_count": 0,
                "feedback": feedback,
            }
        )
    else:
        validity_invalid_count = state.get("validity_invalid_count", 0) + 1
        if validity_invalid_count >= 5:
            return Command(
                goto="result_analysis",
                update={
                    "validity_invalid_count": 0,
                    "feedback": feedback,
                }
            )
        writer_model = get_writer_model()
        content = rewrite_prompt.format(question=question)
        response = writer_model.invoke([HumanMessage(content)])
        new_question = response.content
        return Command(
            goto="generate_computing_code",
            update={
                "question": new_question,
                "validity_invalid_count": validity_invalid_count,
                "feedback": feedback,  
            }
        )


def result_analysis(
    state: KcState,
    analysis_prompt: str = RESULT_ANALYSIS_PROMPT,
    name_prompt: str = RESULT_NAME_PROMPT,
):
    """Analyze the result."""

    question = state.get("question", "")
    figure_id = state.get("figure_id", 0)
    output_dir = state.get("output_dir", "")
    table_info = state.get("table_info", [])
    vl_model = get_analyzer_model()
    writer_model = get_writer_model()

    figure_path = os.path.join(output_dir, "figures", f"fig_{figure_id}.png")

    if os.path.exists(figure_path):
        with open(figure_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        text_content = analysis_prompt.format(
            question=question,
            table_title=table_info[0].get("title", "") if table_info else "",
        )
        content = [
            {
                "type": "text",
                "text": text_content
            },
            {
                "type": "image",
                "source_type": "base64",
                "data": image_data,
                "mime_type": "image/png",
            }
        ]
        desc = ""
        last_analysis_error = None
        for _ in range(1, 4):
            try:
                response = vl_model.invoke([HumanMessage(content)])
                desc = str(response.content).strip()
                if desc:
                    break
                last_analysis_error = RuntimeError("Empty figure analysis response")
            except Exception as e:
                last_analysis_error = e
        if not desc:
            raise RuntimeError(
                "Figure analysis is required but failed after 3 attempts"
            ) from last_analysis_error

        content = name_prompt.format(
            question=question,
            desc=desc,
        )
        try:
            response = writer_model.invoke([HumanMessage(content)])
            name = response.content
        except Exception:
            name = f"Generated Figure {figure_id}"

        relative_path = f"static/{os.path.basename(output_dir)}/figures/fig_{figure_id}.png"
        analysis_result = {
            "name": name,
            "desc": desc,
            "path": relative_path,
        }

    else:
        analysis_result = {
            "name": "",
            "desc": "",
            "path": "",
        }

    return {
        "result": analysis_result,
        "table_info": table_info,
    }


def code_debug(
    history: list[dict],
    prompt: str = CODE_FIX_PROMPT,
) -> str:
    """Fix the code with the given history."""
    history_content = ""
    for item in history:
        history_content += (
            f"---\nattempt {item['attempt_num']}:\n"
            f"code:\n{item['code']}\n"
            f"error:\n{item['error']}\n\n"
        )

    model = get_coder_model()
    content = prompt.format(history_content=history_content)
    response = model.invoke([SystemMessage(content=content)])

    computing_code = ""
    code_blocks = re.findall(r"```python\n([\s\S]*?)\n```", response.content)

    if code_blocks:
        for code_block in code_blocks:
            computing_code += code_block + "\n"
    else:
        computing_code = response.content + "\n"

    return computing_code

def execute_user_code(
    temp_file_path: str
) -> Tuple[Optional[ModuleType], str, Optional[str]]:
    """
    Execute user code in a subprocess and capture stdout / stderr.
    The user code is executed exactly once.
    """
    user_module = None
    error_message = None
    output = ""

    try:
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=30  # 30-second timeout.
        )

        output = result.stdout

        if result.returncode != 0:
            error_message = result.stderr

    except Exception:
        error_message = traceback.format_exc()

    return user_module, output, error_message
