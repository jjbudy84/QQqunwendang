from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from backend.rag_service import RagService


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".txt", ".doc", ".docx"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

rag = RagService(upload_dir=UPLOAD_DIR, data_dir=DATA_DIR)


def json_error(message: str, status_code: int = 400, **extra: Any):
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status_code


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def storage_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    safe_name = secure_filename(filename)
    safe_path = Path(safe_name)

    if safe_path.suffix.lower() != suffix:
        safe_stem = safe_path.stem if safe_path.suffix else safe_name
        if safe_stem.lower() == suffix.lstrip("."):
            safe_stem = ""
        safe_stem = safe_stem or "uploaded_file"
        safe_name = f"{safe_stem}{suffix}"

    candidate = safe_name
    counter = 1
    while (UPLOAD_DIR / candidate).exists():
        path = Path(safe_name)
        candidate = f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    return candidate


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "preview.html")


@app.get("/preview.html")
def preview():
    return send_from_directory(BASE_DIR, "preview.html")


@app.get("/assets/<path:filename>")
def assets(filename: str):
    return send_from_directory(BASE_DIR / "assets", filename)


@app.post("/upload")
def upload():
    file = request.files.get("file")
    if file is None or file.filename == "":
        return json_error("请在 multipart/form-data 中提交名为 file 的文件。")

    if not allowed_file(file.filename):
        return json_error("仅支持 PDF、PPT/PPTX、TXT、Word DOC/DOCX 文件。")

    safe_name = storage_filename(file.filename)
    if not safe_name:
        return json_error("文件名无效。")

    saved_path = UPLOAD_DIR / safe_name
    file.save(saved_path)

    try:
        result = rag.index_file(saved_path, original_name=file.filename)
    except Exception as exc:
        return json_error(f"文件已保存，但解析或索引失败：{exc}", status_code=500)

    return jsonify(
        {
            "ok": True,
            "filename": file.filename,
            "stored_as": saved_path.name,
            "chunks": result["chunks"],
            "characters": result["characters"],
        }
    )


@app.post("/ask")
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or data.get("query") or "").strip()
    if not question:
        return json_error("请提交 JSON：{ \"question\": \"你的问题\" }。")

    try:
        result = rag.answer(question)
    except Exception as exc:
        return json_error(f"问答失败：{exc}", status_code=500)

    return jsonify(
        {
            "answer": result["answer"],
            "sources": result["sources"],
        }
    )


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
