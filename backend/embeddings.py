from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Iterable


class LocalHashEmbedding:
    """Small deterministic embedding fallback so the app works without API keys."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAIEmbedding:
    def __init__(self):
        from openai import OpenAI

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    def __call__(self, input: Iterable[str]) -> list[list[float]]:
        texts = list(input)
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


def build_embedding_function():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbedding()
    return LocalHashEmbedding()
