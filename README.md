# HKA: Hybrid Knowledge Analysis

This repository contains the code for **HKA (Hybrid Knowledge Analysis)**, the framework proposed in the paper:

**Towards Knowledgeable Deep Research: Framework and Benchmark**  
arXiv: [2604.07720](https://arxiv.org/abs/2604.07720)

HKA is a multi-agent framework for Knowledgeable Deep Research (KDR). Given an expert-level research question, the system decomposes it into subtasks, searches unstructured web content, retrieves structured table knowledge, generates executable analysis code, produces figures, and writes a coherent multimodal research report.


## Environment Setup

We recommend using Python 3.10 or later.

```bash
cd HKA
python -m venv .venv
source .venv/bin/activate
```

Install the main dependencies with:

```bash
pip install -r requirements.txt
```

## Configuration

Runtime configuration is read from environment variables. For local development,
copy the example file and fill in your own credentials:

```bash
cp .env.example .env
```

The configuration defaults are defined in:

```text
kdr/config.py
```

Important fields include:

- `INSTANCE_FILE_PATH`: path to the structured table database JSON file.
- `INSTANCE_INDEX_PATH`: path to the FAISS index for table retrieval.
- `NLTK_DATA_PATH`: local NLTK data directory.
- `DEFAULT_LLM_API_KEY`, `DEFAULT_LLM_BASE_URL`: shared defaults for LLM-compatible providers.
- `DEFAULT_CHAT_MODEL`, `DEFAULT_VISION_MODEL`, `DEFAULT_EMBEDDING_MODEL`: shared default model names.
- `WRITER_MODEL`, `CODER_MODEL`, `PLANNER_MODEL`, `ANALYZER_MODEL`: models used by different agents.
- `*_API_KEY`, `*_BASEURL`: model API keys and endpoints.
- `SERPER_API_KEY` or `SEARCH_API_KEY`: web search API key.
- `TOTAL_TOOL_CALL`: maximum number of tool calls in the main workflow.
- `WEB_SEARCH_TOP_K`: number of webpages to retrieve per search query.
- `INSTANCE_TOP_K`, `INSTANCE_SELECTION_K`: table retrieval and selection settings.

## Running HKA

The default entry point is:

```bash
cd HKA
python -m kdr.run
```

The research questions are defined in `kdr/run.py`:

```python
QUESTION_ITEMS = [
    {
        "key": "your_unique_key",
        "question": "Your research question here",
    }
]
```

Edit `QUESTION_ITEMS` to run HKA on your own question.

## Structured Knowledge Analyzer

The workflow for Structured Knowledge Analyzer are listed in:
```
HKA/kdr/tools/knowledge_computing.py
```


## Unstructured Knowledge Analyzer

The workflow for Unstructured Knowledge Analyzer are listed in:
```
HKA/kdr/tools/web_search.py
```


## Quick Start

```bash
cd HKA

# Run the default research question
python -m kdr.run

# Find recent outputs
ls -lt static | head
```

## Citation

If you find this repository useful, please cite our paper:

```bibtex
@misc{liu2026knowledgeabledeepresearch,
  title         = {Towards Knowledgeable Deep Research: Framework and Benchmark},
  author        = {Liu, Wenxuan and Li, Zixuan and Bai, Long and Zhang, Chunmao and Zhang, Fenghui and Chen, Zhuo and Li, Wei and Zuo, Yuxin and Wang, Fei and Xu, Bingbing and Jiang, Xuhui and Zhang, Jin and Jin, Xiaolong and Guo, Jiafeng and Chua, Tat-Seng and Cheng, Xueqi},
  year          = {2026},
  eprint        = {2604.07720},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  doi           = {10.48550/arXiv.2604.07720},
  url           = {https://arxiv.org/abs/2604.07720}
}
```
