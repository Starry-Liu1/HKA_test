"""Knowledge computing."""

import base64
import contextlib
import importlib
import io
import os
import re
import time
import traceback
from functools import partial
from types import ModuleType
from typing import Annotated, Any, Literal, Optional, Tuple
from langchain_core.documents.base import Document
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from kdr.config import (INSTANCE_INDEX_PATH,
                        INSTANCE_SCORE_THRESHOLD, INSTANCE_TOP_K, INSTANCE_SELECTION_K,
                        MAX_OUTPUT_RETRY,INSTANCE_FILE_PATH)
from kdr.model import (QwenEmbedding, get_analyzer_model, get_coder_model,
                       get_extractor_model, get_writer_model)
from kdr.prompts import (CODE_FIX_PROMPT, CODE_GENERATION_PROMPT,
                         EXTRACT_ENTITIES_PROMPT, QUESTION_REWRITE_PROMPT,
                         RESULT_ANALYSIS_PROMPT, RESULT_NAME_PROMPT,
                         RESULT_VALIDITY_PROMPT, CODE_GENERATION_PROMPT_WHOLE_DATA,
                         RERANK_PROMPT)
from kdr.state import ExtractionResults, KcInputState, KcOutputState, KcState
from kdr.utils import format_computing_result, get_logger
import json
def get_instance_from_table_title(table_title: str):
    with open(INSTANCE_FILE_PATH, "r", encoding="utf-8") as f:
        instances = json.load(f)
    for instance in instances:
        if instance["table_title"] == table_title:
            return instance
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
    figures = state.get("figures", [])
    used_tables = state.get("used_tables", [])
    log_file = state.get("log_file", None)

    table_info = state.get("table_info", [])
    logger = get_logger("kdr.knowledge_computing", log_file)

    print("=== STARTING KNOWLEDGE COMPUTING WORKFLOW ===")
    print(f"Output directory: {output_dir}")
    print(f"Figure ID: {figure_id}")
    print(f"Used tables: {used_tables}")
    logger.info(f"Knowledge Computing with figure_id: {figure_id}")
    logger.info("=== Knowledge Computing ===")

    # Generate figure
    print("\n=== INITIATING KNOWLEDGE COMPUTING AGENT ===")
    agent = knowledge_computing_agent()

    print("Invoking knowledge computing agent...")
    print(f"Passing figure_id {figure_id} to agent")
    response = agent.invoke(
        {
            "question": question,
            "output_dir": output_dir,
            "figure_id": figure_id,
            "log_file": log_file,  # 传递log_file以便调试
            "used_tables": used_tables,  # 传递已使用的表格列表
            # 初始化其他必需字段
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

    print("\n=== PROCESSING RESULTS ===")

    # Result validation

    #print(result)
    content = format_computing_result(result, base_url)
    if content is not None:
        figure_id += 1
        figures.append(result)
        #print(content)
        print(f"✅ Successfully generated figure and analysis")
        print(f"New figure ID: {figure_id}")
    else:
        content = (
            "Fail to generate figure and analysis result. "
            "Try to modify the question, use other tools or complete this subtask.\n"
        )
        print(f"❌ Failed to generate valid result")

    print(f"\n=== KNOWLEDGE COMPUTING COMPLETE ===")
    print(f"Final figure ID: {figure_id}")
    print(f"Total figures: {len(figures)}")

    logger.info(
        "Figure:\n"
        "%s\n",
        content,
    )

    # Extract table titles from result and update used_tables
    new_used_tables = used_tables.copy()


    #print(f"Results: {result}")
    #print(f"Table info: {table_info}")
   # if isinstance(result, dict) and "table_info" in result:
    for table in table_info:
        table_title = table.get("title", "")
        table_name = table.get("name", "")
        if table_title and table_title not in new_used_tables:
            new_used_tables.append(table_title)
       # if table_name and table_name not in new_used_tables:
       #     new_used_tables.append(table_name)

    return Command(update={
        "figure_id": figure_id,
        "history": [ToolMessage(content, tool_call_id=tool_call_id)],
        "used_tables": new_used_tables,
        "feedback":""
    })

def knowledge_computing_agent():
    """Knowledge computing agent."""
    # Graph Builder

    builder = StateGraph(
        KcState,
        input_schema=KcInputState,
        output_schema=KcOutputState,
    )
    
    # Nodes
    #builder.add_node("recognize_entities", recognize_entities)
    builder.add_node(
        "search_instances",
        partial(search_instances),
    )
    # Commented out concept search node as we skip concept retrieval
    # builder.add_node(
    #     "search_concepts",
    #     partial(search_concepts, retriever=concept_retriever),
    # )
    builder.add_node("rerank_tables", rerank_tables)
    builder.add_node("generate_computing_code", generate_computing_code)
    builder.add_node("execute_with_auto_repair", execute_with_auto_repair)
    builder.add_node(
        "judge_validity",
        judge_validity,
        destinations=("result_analysis", "generate_computing_code"),
    )
    builder.add_node("result_analysis", result_analysis)

    # Edges - Modified to skip concept search and add reranking
    builder.add_edge(START, "search_instances")
   # builder.add_edge("recognize_entities", "search_instances")
    # Skip concept search - go directly from instances to reranking
    builder.add_edge("search_instances", "rerank_tables")
    # Rerank tables before code generation
    builder.add_edge("rerank_tables", "generate_computing_code")
    # builder.add_edge("search_concepts", "generate_computing_code")  # Removed
    builder.add_edge("generate_computing_code", "execute_with_auto_repair")
    builder.add_edge("execute_with_auto_repair", "judge_validity")
    # Just for hint
    # builder.add_edge("judge_validity", "generate_computing_code")
 #   builder.add_edge("judge_validity", "result_analysis")
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

    print(f"\n=== STEP: RERANKING TABLES ===")
    print(f"Found {len(table_info)} tables, need to select top {top_k}")

    # If we have fewer tables than top_k, return all
    if len(table_info) <= top_k:
        print(f"Only {len(table_info)} tables available, skipping reranking")
        return {"table_info": table_info}

    # Prepare table summaries for LLM
    table_summaries = []
    for i, table in enumerate(table_info):
        summary = f"""
Table {i}:
- Title: {table['title']}
- Content: {table['content'][:1000]}...
"""
        table_summaries.append(summary)

    # Create selection prompt
    summary_data = "".join(table_summaries)
    selection_prompt = RERANK_PROMPT.format(
        question=question,
        summary_data=summary_data,
        top_k=top_k
    )
    print("Selecting relevant tables...")

    try:
        # Get analyzer model for selection
        analyzer_model = get_writer_model()

        # Create messages for the model
        messages = [
            SystemMessage(content="You are an intelligent table selector that responds with valid JSON only."),
            HumanMessage(content=selection_prompt)
        ]

        # Get model response
        response = analyzer_model.invoke(messages)
        response_text = response.content.strip()
        # Parse JSON response
        import json
        try:
            selection_data = json.loads(response_text)
            selected_indices = selection_data.get("selected_indices", [])

            # Validate indices
            valid_indices = []
            for idx in selected_indices:
                if 0 <= idx < len(table_info):
                    valid_indices.append(idx)

            # Ensure we don't exceed top_k and remove duplicates
            valid_indices = list(dict.fromkeys(valid_indices))[:top_k]

            selected_tables = [table_info[i] for i in valid_indices]
            if selected_tables == []:
                selected_tables = table_info[:top_k]

            print(f"Selected {len(selected_tables)} tables: {[t['title'] for t in selected_tables]}")
            logger.info(f"LLM selected {len(selected_tables)} tables out of {len(table_info)}")

            return {"table_info": selected_tables}

        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response length: {len(response_text)} characters")
            logger.warning(f"JSON parsing failed, falling back to simple truncation: {e}")

    except Exception as e:
        print(f"Error during intelligent table selection: {e}")
        logger.warning(f"Intelligent selection failed, falling back to simple truncation: {e}")

    # Fallback to simple truncation if intelligent selection fails
    print(f"Falling back to simple truncation: taking first {top_k} tables")
    return {"table_info": table_info[:top_k]}


def search_instances(
    state: KcState,
    #retriever: Any = None,
):
    """Search relevant table instances."""
   # entities = state.get("entities", [])


    log_file = state.get("log_file", None)
    used_tables = state.get("used_tables", [])

    print(f"\n=== STEP: SEARCHING FOR TABLE INSTANCES ===")
    emb = QwenEmbedding()
    db = FAISS.load_local(
    INSTANCE_INDEX_PATH,
    embeddings=emb,
    allow_dangerous_deserialization=True,
    )
    retriever = db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
        "k": INSTANCE_TOP_K+len(used_tables),
        "score_threshold": INSTANCE_SCORE_THRESHOLD,
    }
    )
    
    

    question = state.get("question", "")
    logger = get_logger("kdr.knowledge_computing", log_file)

    print(f"Already used tables: {used_tables}")
#    print(f"Extracted entities: {[e['name'] for e in entities]}")

    # Retrieve instances (now representing tables/DataFrames)
    instances = []
    #print(f"Searching for tables using question: {question}")
    entity_results_old = retriever.invoke(question)
    #print(f"Found {len(entity_results_old)} potential table instances")
    entity_results = []
    for result in entity_results_old:
        table_title = result.metadata.get('table_title', '')
        instance =get_instance_from_table_title(table_title)
        #print(instance)
        doc =Document(
                page_content=table_title,
                metadata=instance,
            )
        entity_results.append(doc)
    for result in entity_results:
        table_title = result.metadata.get('table_title', '')
        table_name = result.metadata.get('table_name', '')
        # Skip if this table has been used before
        if table_title in used_tables or table_name in used_tables:
            print(f"  - Skipping already used table: {table_title or table_name}")
            continue

        if result not in instances:
            instances.append(result)
            print(f"  - Added new table: {table_title or table_name}")
    '''
    for entity in entities:
        print(f"Searching for tables related to entity: {entity['name']}")
        entity_results = retriever.invoke(entity["name"])
        print(f"Found {len(entity_results)} potential table instances")
        for result in entity_results:
            if result not in instances:
                instances.append(result)
                print(f"  - Added table: {result.metadata.get('table_name', 'Unknown')}")
    '''
    print(f"Total unique tables found: {len(instances)}")

    # Construct code to load and prepare tables
    instances_code = "# Import necessary libraries for data handling\n"
    instances_code += "import matplotlib\n"
    instances_code += "matplotlib.use('Agg')  # Use non-interactive backend to prevent thread issues\n"
    instances_code += "import matplotlib.pyplot as plt\n"

    # Track table information for code generation
    table_info = []

    for i, instance in enumerate(instances):
        #print(instance)
        
        table_name = instance.metadata.get("table_name", f"table_{i}")
        table_path = instance.metadata.get("file_path", "")
        table_title = instance.metadata.get("table_title", "")
        table_content = instance.metadata.get("table_data", "")
        table_data_model = instance.metadata.get("python_parsing_code", "Unknown")
        table_code_test_result = instance.metadata.get("code_test_result", "Unknown")
        #table_type = instance.metadata.get("table_type", "csv")
        output_data_comments = instance.metadata.get("output_data_comments", "")
        if table_title in used_tables:
            print(f"  - Skipping already used table in info collection: {table_title or table_name}")
            continue

        print(f"\nProcessing table {i+1}: {table_title}")
       # print(f"  - Type: {table_content}")

        # Add code to parse the string table data into DataFrame
        

        # Store table info for later use
        
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

    # Enhanced assertion code - validate tables are properly loaded as DataFrames
    assertion_code = ""
    '''
    for table in table_info:
        table_name = table["name"]

        assertion_code += f"assert isinstance({table_name}, pd.DataFrame), f'{table_name} should be a DataFrame'\n"
        assertion_code += f"assert len({table_name}) > 0, f'{table_name} should not be empty'\n"
        assertion_code += f"print(f'{{len({table_name})}} rows in {table_name} with columns: {{list({table_name}.columns)}}')\n"
    '''
    print(f"\nGenerated code for {len(table_info)} tables")

    # Note: Table selection/reranking is now done in a separate rerank_tables node

    # Generate instances code for all tables
    print(f"Processing {len(table_info)} tables for instances code")
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
        "table_info": table_info,  # Pass table info to code generation
    }


def search_concepts(
    state: KcState,
    retriever: Any,
):
    """Search relevant concepts."""
    entities = state.get("entities", [])
    log_file = state.get("log_file", None)
    logger = get_logger("kdr.knowledge_computing", log_file)

    # Retrieve concepts
    concept_ids = set()
    for entity in entities:
        # Avoid adding duplicate concepts by concept_name
        retrieved = retriever.invoke(entity["name"])
        for concept in retrieved:
            if concept.metadata.get("concept_id", "") not in concept_ids:
                concept_ids.add(concept.metadata.get("concept_id"))
                ref_concept_ids = concept.metadata.get("reference_concept_id", "")
                if ref_concept_ids:
                    ref_concept_ids = ref_concept_ids.split(",")
                    concept_ids = concept_ids.union(
                            [int(_) for _ in ref_concept_ids]
                        )

    # Obtain all concepts that ids are in concept_ids.
    concepts = [_ for _ in list(retriever.vectorstore.docstore._dict.values())
                if _.metadata.get("concept_id", "") in concept_ids]

    # Construct python code for concepts
    concepts_code = "\n\n".join([
        concept.metadata.get("code", "") for concept in concepts
    ])

    concepts_code = (
        "from typing import List\n"
        "\n"
        "# Class definition code\n"
        "class Entity:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "class Relation:\n"
        "   # Base class for all relations\n"
        "   def __init__(self, object_names, *objects):\n"
        "       self.objects = {}\n"
        "       for object_name, object_value in zip(object_names, objects):\n"
        "           self.objects[object_name] = object_value\n"
        "class Event:\n"
        "   # Base class for all events\n"
        "   def __init__(self, arg_names, *args):\n"
        "       self.arguments = {}\n"
        "       for arg_name, arg_value in zip(arg_names, args):\n"
        "            self.arguments[arg_name] = arg_value\n"


        f"{concepts_code}\n"
    )
    logger.info(
        "Searched concepts:\n"
        "%s\n",
        ", ".join([c.metadata.get("concept_name", "") for c in concepts])
    )

    return {
        "concepts_code": concepts_code,
    }


def generate_computing_code(
    state: KcState,
    prompt: str = CODE_GENERATION_PROMPT,
   # feedback: str = "",  # Default feedback parameter
):
    """Generate code for the question based on table data."""
    feedback=state.get("feedback", "")
    question = state.get("question", "")
    output_dir = state.get("output_dir", "")
    figure_id = state.get("figure_id", 0)
    instances_code = state.get("instances_code", "")  # Table loading code
    assertion_code = state.get("assertion_code", "")
    table_infos = state.get("table_info", [])  # Information about available tables

    # Get feedback from state if available
    state_feedback = state.get("feedback", "")
    if state_feedback:
        feedback = state_feedback

    #print(table_infos)
    table_info=table_infos[0]

    used_tables = state.get("used_tables", [])

    # Print feedback if available
    if feedback:
        print("Previous attempt feedback is available")
    for i,table_datum in enumerate(table_infos):
        if table_datum['title'] not in state.get("used_tables", []):
            table_info = table_infos[i]

    
    #print(table_info) 

    table_code_test_result = table_info.get("table_code_test_result", "Unknown")
    output_data_comments = table_info.get("output_data_comments", "")
    table_data = table_info.get("content", "")
    print("=== STEP: GENERATING COMPUTING CODE ===")
    print(f"Table title {table_info['title']}")
    print(f"Figure ID: {figure_id}")
    print(f"CODE GENERATION: Will generate code for figure_{figure_id}.png")

    # Generate computing code

    #python_code =  table_info['table_data_model'].replace(table_data)
    #python_code = table_info['table_data_model'].replace(table_data,"{{table_data}}")

    model = get_coder_model()
    figure_dir = os.path.join(output_dir, "figures")
    os.makedirs(figure_dir, exist_ok=True)
    #print(table_code_test_result)
    # Create detailed table descriptions for better code generation

    '''
    table_descriptions = ""
    for i, table in enumerate(table_info):
        table_descriptions += f"\n{i+1}. table_data_{i}:\n"
        table_descriptions += f"   - Title: {table['title']}\n"
        table_descriptions += f"   - Domain: {table['domain']}\n"
        table_descriptions += f"   - Sub-domain: {table['sub_domain']}\n"
        table_descriptions += f"   - Topic: {table['topic']}\n"
        table_descriptions += f"   - Path: {table['path']}\n"
        #if table['content']:
        #    table_descriptions += f"   - Data: Available as inline content\n"
        #    table_descriptions += f"   - Content: {table['content']}\n"
    '''
    # Create a custom prompt that includes detailed table information
    import json
    if "success" in table_code_test_result and table_code_test_result['success']==True:
        output_data_comments =output_data_comments
        
        if output_data_comments:
            give_data =json.dumps(table_code_test_result.get("output_data",{}), indent=2)
            # Build a small sample: for dicts, take first 3 values of each list; for lists, take first 3 items
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
            
        custom_prompt = CODE_GENERATION_PROMPT.format(
            question=question,
            output_data_comments=output_data_comments,
            data_sample=data_sample,
            instance_code=instances_code,
            figure_dir=figure_dir,
            figure_id=figure_id,
        )    
        
    
    
    else:
        # Add feedback context if available
        custom_prompt=CODE_GENERATION_PROMPT_WHOLE_DATA.format(
            question=question,
            instances_code=instances_code,
            figure_dir=figure_dir,
            figure_id=figure_id,
        )

    
    
    print("\nSending prompt to code generation model...")
    print(f"Prompt length: {len(custom_prompt)} characters")
    # Do not print the full prompt; it can contain large table data and code.
    #print()
    response = model.invoke([HumanMessage(content=custom_prompt)])
   # print(response.content)
    print("Received response from model")
    computing_code = "# Computing code generated based on tables\n"
    
    # Extract code blocks (with or without markdown formatting)
    code_blocks = re.findall(r"```python\n([\s\S]*?)\n```", response.content)
    if not code_blocks:
        # Try to extract code without markdown tags
        code_blocks = [response.content]

    for code_block in code_blocks:
        computing_code += code_block + "\n"
    if "output_data_place_holder" in computing_code:
        computing_code = computing_code.replace("output_data_place_holder", json.dumps(table_code_test_result.get("output_data",{}), indent=2))
    if "{{output_data}}" in computing_code:
        computing_code = computing_code.replace("{{output_data}}", json.dumps(table_code_test_result.get("output_data",{}), indent=2))

    
    print(f"Generated computing code length: {len(computing_code)} characters")
   # print(f"Code contains 'plt.savefig': {'plt.savefig' in computing_code}")
   # print(f"Code contains figure directory reference: {figure_dir in computing_code}")
    #print(computing_code)

    return {
        "computing_code": computing_code,
        "table_info": [table_info] if isinstance(table_info, dict) else table_info,
    }


def execute_with_auto_repair(
    state: KcState,
):
    """Execute the generated code."""
    output_dir = state.get("output_dir", 0)
    figure_id = state.get("figure_id", 0)
    instances_code = state.get("instances_code", "")
    assertion_code = state.get("assertion_code", "")
    computing_code = state.get("computing_code", "")
    table_info = state.get("table_info", [])  # Get table_info to pass through

    print("=== STEP: EXECUTING CODE WITH AUTO-REPAIR ===")
    print(f"Figure ID: {figure_id}")
    print(f"CODE EXECUTION: Will save code to runnable_code_{figure_id}.py")

    code_history = []
    attempt_num = 0
    output = None
    error = None
    while attempt_num < 5:
        print(f"\n--- Attempt {attempt_num + 1}/5 ---")

        # Construct runnable code (without concepts_code)
        runnable_code = (
            f"{computing_code}\n"
        )

        # Save the runnable code to file
        code_file_path = os.path.join(output_dir, f"runnable_code_{figure_id}.py")
        with open(code_file_path, "w", encoding="utf-8") as f:
            f.write(runnable_code)

        print(f"Code saved to: {code_file_path}")
        print(f"Total code length: {len(runnable_code)} characters")

        # Execute the code
        print("Executing code...")
        _, output, error = execute_user_code(code_file_path)

        if error:
            print(f"❌ Execution failed with error:")
            print(error)
        else:
            print(f"✅ Execution successful!")
            if output:
                print(f"Output length: {len(output)} characters")
                # Avoid dumping generated script output into the main log.

        # Save history record
        code_history.append({
            "code": runnable_code,
            "output": output,
            "error": error,
            "attempt_num": attempt_num,
        })

        if error and attempt_num < 5:  # Allow one more attempt for debugging
            print("Attempting to fix the code...")
            computing_code = code_debug(code_history)
            print(f"Generated new code of length: {len(computing_code)} characters")
        else:
            break
        attempt_num += 1

    print(f"\n=== EXECUTION COMPLETE ===")
    print(f"Total attempts: {attempt_num}")
    print(f"Final status: {'SUCCESS' if not error else 'FAILED'}")

    return {
        "result": output if not error else error,
        "table_info": table_info,  # Pass table_info through
    }


def judge_validity(
    state: KcState,
    validity_prompt: str = RESULT_VALIDITY_PROMPT,
    rewrite_prompt: str = QUESTION_REWRITE_PROMPT,
) -> Command[Literal["result_analysis", "generate_computing_code"]]:
    """Judge validity."""

    print("=== STEP: JUDGING RESULT VALIDITY ===")
    question = state.get("question", "")
    figure_id = state.get("figure_id", 0)
    output_dir = state.get("output_dir", "")

    # Analyze the result
    figure_path = os.path.join(output_dir, "figures", f"fig_{figure_id}.png")
    #print(figure_path)
    # if figure_path exists, load and analyze
    vl_model = get_analyzer_model()
    #print(figure_path)

    # Initialize feedback
    feedback = ""

    if os.path.exists(figure_path):
        # Generate figure analysis
        #print(figure_path)

        with open(figure_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        text_content = validity_prompt.format(
            question=question,
        )

       # print(text_content)
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
            judge_start_time = time.time()
            response = vl_model.invoke([HumanMessage(content)])
            print(f"Validity judge took {time.time() - judge_start_time:.2f}s")
            print(f"Validity judge response: {repr(response.content)}")

            # Parse response robustly. The model is asked to return True/False, but
            # providers may include whitespace or short surrounding text.
            judge_result = str(response.content).strip()
        except Exception as e:
            feedback = f"Validity judge API failed or timed out: {type(e).__name__}: {e}"
            print(feedback)
            print("Skipping validity judge and continuing with current figure.")
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
        print("✅ Figure judged as VALID")
        return Command(
            goto="result_analysis",
            update={
                "validity_invalid_count": 0,
                "feedback": feedback,  # Include feedback even for valid results
            }
        )
    else:
        validity_invalid_count = state.get("validity_invalid_count", 0) + 1
        print(f"❌ Figure judged as INVALID ({validity_invalid_count}/5)")
        print(f"Feedback: {feedback}")
        if validity_invalid_count >= 5:
            print("Reached 5 invalid judgments; accepting current figure and continuing.")
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
        print("Rewritten question for next attempt")
        return Command(
            goto="generate_computing_code",
            update={
                "question": new_question,
                "validity_invalid_count": validity_invalid_count,
                "feedback": feedback,  
            }
        )
    #'''


def result_analysis(
    state: KcState,
    analysis_prompt: str = RESULT_ANALYSIS_PROMPT,
    name_prompt: str = RESULT_NAME_PROMPT,
):
    """Analyze the result."""

    print("=== STEP: ANALYZING RESULT ===")
    question = state.get("question", "")
    figure_id = state.get("figure_id", 0)
    output_dir = state.get("output_dir", "")
    table_info = state.get("table_info", [])  # Get table info to return it
    vl_model = get_analyzer_model()
    writer_model = get_writer_model()

    # Analyze the result
    figure_path = os.path.join(output_dir, "figures", f"fig_{figure_id}.png")

    # if figure_path exists, load and analyze
    if os.path.exists(figure_path):
        print(f"✅ Figure generated successfully: {figure_path}")

        # Generate figure analysis
        with open(figure_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        #print(table_info[0].keys())
        text_content = analysis_prompt.format(
            question=question,
            table_title=table_info[0]['title'] if len(table_info) > 0 else "",
        )
        #print(text_content)
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
        for analysis_attempt in range(1, 4):
            try:
                analysis_start_time = time.time()
                print(f"Figure analysis attempt {analysis_attempt}/3")
                response = vl_model.invoke([HumanMessage(content)])
                print(f"Figure analysis took {time.time() - analysis_start_time:.2f}s")
                desc = str(response.content).strip()
                if desc:
                    break
                last_analysis_error = RuntimeError("Empty figure analysis response")
                print("Figure analysis returned an empty response.")
            except Exception as e:
                last_analysis_error = e
                print(
                    "Figure analysis failed or timed out: "
                    f"{type(e).__name__}: {e}"
                )
        if not desc:
            raise RuntimeError(
                "Figure analysis is required but failed after 3 attempts"
            ) from last_analysis_error

        # Generate figure name
        content = name_prompt.format(
            question=question,
            desc=desc,
        )
        try:
            name_start_time = time.time()
            response = writer_model.invoke([HumanMessage(content)])
            print(f"Figure name generation took {time.time() - name_start_time:.2f}s")
            name = response.content
        except Exception as e:
            name = f"Generated Figure {figure_id}"
            print(
                "Figure name generation failed or timed out: "
                f"{type(e).__name__}: {e}"
            )

        # Construct analysis result
        # Store relative path instead of absolute path for proper URL generation
        # output_dir format: /path/to/project/static/{report_id}
        # We need: static/{report_id}/figures/fig_{figure_id}.png
        relative_path = f"static/{os.path.basename(output_dir)}/figures/fig_{figure_id}.png"
        analysis_result = {
            "name": name,
            "desc": desc,
            "path": relative_path,
        }

    else:
        print(f"❌ Figure generation failed: {figure_path} does not exist")
        analysis_result = {
            "name": "",
            "desc": "",
            "path": "",
        }

    return {
        "result": analysis_result,
        "table_info": table_info,  # Also return table_info so we can track used tables
    }


def code_debug(
    history: list[dict],
    prompt: str = CODE_FIX_PROMPT,
) -> str:
    """Fix the code with the given history."""
    print("=== STEP: DEBUGGING CODE ===")
    print(f"Debugging with {len(history)} previous attempts")

    history_content = ""
    for item in history:
        print(f"  Attempt {item['attempt_num']}: {'ERROR' if item['error'] else 'SUCCESS'}")
        history_content += (
            f"---\nattempt {item['attempt_num']}:\n"
            f"code:\n{item['code']}\n"
            f"error:\n{item['error']}\n\n"
        )

    print(f"Sending debugging history to model (length: {len(history_content)} chars)...")
    model = get_coder_model()
    content = prompt.format(history_content=history_content)
    response = model.invoke([SystemMessage(content=content)])

    print("Received debugging response from model")
    computing_code = ""
    code_blocks = re.findall(r"```python\n([\s\S]*?)\n```", response.content)

    if code_blocks:
        for code_block in code_blocks:
            computing_code += code_block + "\n"
    else:
        # If no code blocks found, use the entire response
        computing_code = response.content + "\n"

    print(f"Generated fixed code length: {len(computing_code)} characters")
    return computing_code


import subprocess
import sys
import traceback
from types import ModuleType
from typing import Optional, Tuple


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
            timeout=30  # 10秒超时
        )

        output = result.stdout

        if result.returncode != 0:
            error_message = result.stderr

    except Exception:
        error_message = traceback.format_exc()

    return user_module, output, error_message
