from __future__ import annotations

import re
import uuid
from pathlib import Path

from backend.document_parser import parse_document
from backend.embeddings import build_embedding_function
from backend.llm import generate_answer
from backend.vector_store import LocalVectorStore


class RagService:
    def __init__(self, upload_dir: Path, data_dir: Path):
        self.upload_dir = upload_dir
        self.embedding_function = build_embedding_function()
        self.store = LocalVectorStore(data_dir / "vector_index.json")

    def index_file(self, path: Path, original_name: str) -> dict[str, int]:
        text = normalize_text(parse_document(path, original_name=original_name))
        if not text:
            raise ValueError("未能从文件中解析出文本内容。")

        chunks = split_text(text)
        file_id = str(uuid.uuid4())
        ids = [f"{file_id}-{index}" for index in range(len(chunks))]
        metadatas = [
            {
                "file_id": file_id,
                "filename": original_name,
                "stored_as": path.name,
                "chunk_index": index,
            }
            for index in range(len(chunks))
        ]

        embeddings = self.embedding_function(chunks)
        self.store.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
        return {"chunks": len(chunks), "characters": len(text)}

    def answer(self, question: str) -> dict[str, object]:
        query_embedding = self.embedding_function([question])[0]
        matches = self.store.query(query_embedding=query_embedding, limit=5)

        context_parts: list[str] = []
        sources: list[dict[str, object]] = []
        for match in matches:
            document = match["document"]
            metadata = match["metadata"]
            filename = metadata.get("filename", "unknown")
            chunk_index = metadata.get("chunk_index", 0)
            context_parts.append(f"[来源：{filename}，片段 {chunk_index}]\n{document}")
            sources.append(
                {
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "score": round(float(match["score"]), 4),
                    "text": document[:300],
                }
            )

        context = "\n\n".join(context_parts)
        answer = clean_answer_format(generate_answer(question=question, context=context))
        return {"answer": answer, "sources": sources}


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_answer_format(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)

    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        line = re.sub(r"^\s*[-*•]\s*", "", line)
        line = re.sub(r"^\s*\d+[.)]\s*", "", line)
        cleaned_lines.append(line.rstrip())

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
