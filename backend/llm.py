from __future__ import annotations

import os


SYSTEM_PROMPT = """你是一个基于用户上传资料回答问题的 AI 助手。
只依据给定资料回答，不要使用资料之外的事实。
如果用户要求“总结、概括、提炼、主要内容、讲了什么”，并且资料内容非空，必须直接总结资料，不要回答“没有找到相关信息”。
只有当资料为空，或资料内容与问题完全无关时，才说“上传资料中没有找到相关信息”。
回答要简洁、准确，必要时引用文件名或页码线索。"""


def generate_answer(question: str, context: str) -> str:
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    if provider == "deepseek" and os.getenv("DEEPSEEK_API_KEY"):
        return generate_with_deepseek(question, context)
    if provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        return generate_with_anthropic(question, context)
    if provider in {"openai", "gpt"} and os.getenv("OPENAI_API_KEY"):
        return generate_with_openai(question, context)
    return generate_local_answer(context)


def generate_with_openai(question: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    return chat_completion(client=client, model=model, question=question, context=context)


def generate_with_deepseek(question: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    return chat_completion(client=client, model=model, question=question, context=context)


def chat_completion(client, model: str, question: str, context: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "下面是从用户上传文件中检索到的资料片段。"
                    "请优先判断这些片段能否回答问题；如果问题是总结类，请直接总结这些片段。\n\n"
                    f"资料：\n{context}\n\n问题：{question}"
                ),
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def generate_with_anthropic(question: str, context: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
    response = client.messages.create(
        model=model,
        max_tokens=1200,
        temperature=0.2,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"资料：\n{context}\n\n问题：{question}",
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def generate_local_answer(context: str) -> str:
    if not context.strip():
        return "上传资料中没有找到相关信息。"
    return (
        "当前未配置 AI API Key，先返回检索到的相关资料片段。"
        "配置 DEEPSEEK_API_KEY、OPENAI_API_KEY 或 ANTHROPIC_API_KEY 后会生成自然语言回答。\n\n"
        f"{context[:1800]}"
    )
