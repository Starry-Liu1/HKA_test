"""Model."""

import time
from typing import List

from langchain_core.language_models import LanguageModelLike
from langchain_openai import ChatOpenAI
from openai import OpenAI

from kdr.config import (BASEURL_EMBEDDING, EMBEDDING_API_KEY,
                        EMBEDDING_DIMENSIONS, EMBEDDING_MODEL,
                        MODEL_CONFIGS, SEED)


def _chat_config(model_role: str) -> dict:
    """Get the model, API key, and base URL for a configured model role."""
    return MODEL_CONFIGS[model_role]


def get_writer_model() -> LanguageModelLike:
    """Get writer model."""
    config = _chat_config("writer")
    return ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        temperature=1,
        seed=SEED,
    )


def get_planner_model() -> LanguageModelLike:
    """Get planner model."""
    config = _chat_config("planner")
    return ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        temperature=1,
        seed=SEED,
    )


def get_coder_model() -> LanguageModelLike:
    """Get coder model."""
    config = _chat_config("coder")
    return ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        temperature=1,
        seed=SEED,
    )


def get_analyzer_model():
    """Get chart analysis model."""
    config = _chat_config("analyzer")
    return ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        seed=SEED,
        timeout=60,
        max_retries=3,
    )

class GenericEmbedding:
    """Generic embedding client."""

    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        dimensions: int = EMBEDDING_DIMENSIONS,
        max_retries: int = 3,
        retry_interval: float = 5.0,
    ):
        self.model = model
        self.dimensions = dimensions
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.client = OpenAI(
            api_key=EMBEDDING_API_KEY,
            base_url=BASEURL_EMBEDDING,
        )

    def embedding_func(self, text: str) -> List[float]:
        """Embedding function."""
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                embedding = self.client.embeddings.create(
                    model=self.model,
                    input=text,
                    dimensions=self.dimensions,
                    encoding_format="float",
                )
                return embedding.data[0].embedding
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_interval)

        raise RuntimeError(
            f"Failed to create embedding after {self.max_retries} attempts"
        ) from last_error

    def __call__(self, text: str) -> List[float]:
        return self.embedding_func(text)

    def embed_documents(self, docs: List[str]) -> List[List[float]]:
        """Embed documents."""
        return [self.embedding_func(doc) for doc in docs]

    def embed_query(self, query: str) -> List[float]:
        """Embed query."""
        return self.embedding_func(query)
