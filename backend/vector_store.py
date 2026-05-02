from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


class LocalVectorStore:
    """A tiny persistent vector store with cosine search.

    It keeps the app dependency-light on Windows/Python 3.13. The rest of the
    RAG code talks to this small boundary, so swapping in ChromaDB or Weaviate
    later only needs changes here.
    """

    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.items = self._load()

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        for item_id, document, embedding, metadata in zip(ids, documents, embeddings, metadatas):
            self.items.append(
                {
                    "id": item_id,
                    "document": document,
                    "embedding": embedding,
                    "metadata": metadata,
                }
            )
        self._save()

    def query(self, query_embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        scored: list[dict[str, Any]] = []
        for item in self.items:
            embedding = item.get("embedding", [])
            if len(embedding) != len(query_embedding):
                continue
            scored.append({**item, "score": cosine_similarity(query_embedding, embedding)})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    def _load(self) -> list[dict[str, Any]]:
        if not self.index_path.exists():
            return []
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.index_path.write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
