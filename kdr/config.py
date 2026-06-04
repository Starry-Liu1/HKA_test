"""Config."""

# PATHS

INSTANCE_FILE_PATH = "./data/databases/all_tables_info_with_code_part_new_comments_0427.json"
INSTANCE_INDEX_PATH = "./data/databases/tables"
NLTK_DATA_PATH = "./nltk_data"
CHECKPOINTS_PATH = "./data/databases/checkpoints.db"

# Langsmith
LANGSMITH_PROJECT = "kdr"

import os

#os.environ['DASHSCOPE_API_KEY'] = "sk-063aa326a43d436faf6c8a1ab97f2ff5"
os.environ['SERPER_API_KEY'] = "a1bc5ce18df87cbe1b224db8b698caa5c387f375"


os.environ['tavily_api_key'] = "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"

# Model
DEFAULT_OPENAI_API_KEY = "sk-LsMa0XzkrIr8YixcA3sau42S0JLR6Wz8ZiW4WL2DOqjVHUtu"
DEFAULT_BASEURL_OPENAI = "https://www.dmxapi.cn/v1"

# Keep legacy names for modules outside kdr that may still import them.
OPENAI_API_KEY = DEFAULT_OPENAI_API_KEY
BASEURL_OPENAI = DEFAULT_BASEURL_OPENAI
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

WRITER_MODEL = "qwen3-235b-a22b-instruct-2507"
WRITER_API_KEY = "sk-LsMa0XzkrIr8YixcA3sau42S0JLR6Wz8ZiW4WL2DOqjVHUtu"
WRITER_BASEURL = "https://www.dmxapi.cn/v1"

CODER_MODEL = "ep-20251215153040-fqgmp"
CODER_API_KEY = "334a2cc2-aadd-4181-aa38-98bab4a5387b"
CODER_BASEURL = "https://ark.cn-beijing.volces.com/api/v3"

PLANNER_MODEL = "ep-20251215153040-fqgmp"
PLANNER_API_KEY = "334a2cc2-aadd-4181-aa38-98bab4a5387b"
PLANNER_BASEURL = "https://ark.cn-beijing.volces.com/api/v3"

ANALYZER_MODEL = "Qwen3-VL-235B-A22B-Instruct"
ANALYZER_API_KEY = "sk-LsMa0XzkrIr8YixcA3sau42S0JLR6Wz8ZiW4WL2DOqjVHUtu"
ANALYZER_BASEURL = "https://www.dmxapi.cn/v1"

EVALUATION_MODEL = "DeepSeek-V3.2-Thinking"
EVALUATION_API_KEY = DEFAULT_OPENAI_API_KEY
EVALUATION_BASEURL = DEFAULT_BASEURL_OPENAI


EVALUATION_MODEL_NO_Thinking = "DeepSeek-V3.2"
EVALUATION_NO_THINKING_API_KEY = DEFAULT_OPENAI_API_KEY
EVALUATION_NO_THINKING_BASEURL = DEFAULT_BASEURL_OPENAI

EVALUATION_MODEL_GPT5_MINI = "gpt-5-mini"
EVALUATION_GPT5_MINI_API_KEY = DEFAULT_OPENAI_API_KEY
EVALUATION_GPT5_MINI_BASEURL = DEFAULT_BASEURL_OPENAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_API_KEY = "sk-SWXwzlaEt0pUPb6apkd820SSNOw5k5Jedmwq8NKK1i1iUkdl"
BASEURL_EMBEDDING = "https://api.chatanywhere.tech/v1"
EMBEDDING_DIMENSIONS = 1024

MODEL_CONFIGS = {
    "writer": {
        "model": WRITER_MODEL,
        "api_key": WRITER_API_KEY,
        "base_url": WRITER_BASEURL,
    },
    "coder": {
        "model": CODER_MODEL,
        "api_key": CODER_API_KEY,
        "base_url": CODER_BASEURL,
    },
    "planner": {
        "model": PLANNER_MODEL,
        "api_key": PLANNER_API_KEY,
        "base_url": PLANNER_BASEURL,
    },
    "analyzer": {
        "model": ANALYZER_MODEL,
        "api_key": ANALYZER_API_KEY,
        "base_url": ANALYZER_BASEURL,
    },
    "evaluation": {
        "model": EVALUATION_MODEL,
        "api_key": EVALUATION_API_KEY,
        "base_url": EVALUATION_BASEURL,
    },
    "evaluation_no_thinking": {
        "model": EVALUATION_MODEL_NO_Thinking,
        "api_key": EVALUATION_NO_THINKING_API_KEY,
        "base_url": EVALUATION_NO_THINKING_BASEURL,
    },
    "evaluation_gpt5_mini": {
        "model": EVALUATION_MODEL_GPT5_MINI,
        "api_key": EVALUATION_GPT5_MINI_API_KEY,
        "base_url": EVALUATION_GPT5_MINI_BASEURL,
    },
}

SEED = 42
MAX_OUTPUT_RETRY = 2

# Supervisor
TOTAL_TOOL_CALL = 30

# Web Search
WEB_SEARCH_TOP_K = 5

# Knowledge Computing
CONCEPT_TOP_K = 5
INSTANCE_TOP_K = 5
INSTANCE_SELECTION_K = 1
INSTANCE_SCORE_THRESHOLD = -1.0  # FAISS uses cosine similarity by default
