# QQ 群聊 RAG 后端

这个后端提供两个接口：

- `POST /upload`：上传 PDF/PPTX/TXT/DOCX，解析文本并写入本地持久化向量索引
- `POST /ask`：接收问题，检索已上传资料，调用 OpenAI 或 Anthropic 生成回答

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

然后打开：

```text
http://127.0.0.1:5000/
```

服务会直接托管当前目录下的 `preview.html`。如果页面里的 JS 使用相对路径调用 `/upload` 和 `/ask`，就会命中这个后端。

## 环境变量

`.env` 中配置 DeepSeek：

```text
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

或使用 OpenAI：

```text
AI_PROVIDER=openai
OPENAI_API_KEY=你的 Key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

或使用 Claude：

```text
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=你的 Key
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
```

未配置 API Key 时，系统仍会保存文件、解析文本、建立本地哈希向量索引，并在提问时返回检索到的相关片段。

默认实现使用 `data/vector_index.json` 作为轻量本地向量库，避免 Windows + Python 3.13 安装 ChromaDB 时的编译问题。要接入 ChromaDB 或 Weaviate，只需要替换 `backend/vector_store.py`，`/upload` 和 `/ask` 的业务接口不用变。

## 接口示例

上传：

```powershell
curl.exe -X POST http://127.0.0.1:5000/upload -F "file=@C:\path\demo.pdf"
```

提问：

```powershell
curl.exe -X POST http://127.0.0.1:5000/ask `
  -H "Content-Type: application/json" `
  -d "{\"question\":\"这份资料主要讲了什么？\"}"
```

返回：

```json
{
  "answer": "AI 回答",
  "sources": []
}
```

## 前端连接约定

文件上传使用 `multipart/form-data`，字段名必须是 `file`。

提问使用 JSON：

```json
{ "question": "你的问题" }
```

当前仓库里的 `preview.html` 是纯静态 UI，没有发现可工作的 `fetch('/upload')`、`fetch('/ask')` 绑定；后端已经准备好接口，页面只要接入这两个相对路径即可。
