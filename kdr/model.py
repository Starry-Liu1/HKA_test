"""Model."""

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


def get_extractor_model() -> LanguageModelLike:
    """Get extractor model."""
    config = _chat_config("extractor")
    return ChatOpenAI(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["base_url"],
      #  enable_thinking=False,
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
       # enable_thinking=True,
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
        dimensions: int = EMBEDDING_DIMENSIONS
    ):
        self.model = model
        self.dimensions = dimensions

    def embedding_func(self, text: str) -> List[float]:
        """Embedding function."""
        client = OpenAI(
            api_key=EMBEDDING_API_KEY,
            base_url=BASEURL_EMBEDDING,
        )
        emb=None
        try:
            emb = client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions,
                encoding_format="float",
            )
        except:
            i=0
            while i<3:
                
                import time
                time.sleep(5)
                emb=None
                try:
                    emb = client.embeddings.create(
                        model=self.model,
                        input=text,
                        dimensions=self.dimensions,
                        encoding_format="float",
                    )
                except:
                    i=i+1
                
                if emb:
                    break
                
        if emb:
            return emb.data[0].embedding
        else:
            return [-99999999999]*self.dimensions

    def __call__(self, text: str) -> List[float]:
        return self.embedding_func(text)

    def embed_documents(self, docs: List[str]) -> List[List[float]]:
        """Embed documents."""
        return [self.embedding_func(doc) for doc in docs]

    def embed_query(self, query: str) -> List[float]:
        """Embed query."""
        return self.embedding_func(query)
