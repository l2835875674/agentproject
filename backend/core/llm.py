"""模型调用封装。换模型只改这里。"""
from typing import List, Optional

from openai import OpenAI

from backend.config import API_KEY, BASE_URL, MODEL

_client: Optional[OpenAI] = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not API_KEY:
            raise RuntimeError("缺少 DEEPSEEK_API_KEY，请在 .env 中配置")
        _client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    return _client


def ask_llm(messages: List[dict], tools: List[dict] = None, temperature: float = 0.7) -> str:
    kwargs = {"model": MODEL, "messages": messages, "temperature": temperature}
    if tools:
        kwargs["tools"] = tools
    resp = client().chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def ask_json(messages: List[dict], temperature: float = 0.2) -> dict:
    """要求模型只输出 JSON，并解析。结构化中间表示都走这里。"""
    import json

    resp = client().chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content
    return json.loads(text)


def build_kwargs(messages, tools=None, cfg=None, stream=False):
    """统一组装请求参数，避免各处重复。"""
    from backend.core import settings as _s
    cfg = cfg or _s.DEFAULT
    kw = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
        "stream": stream,
    }
    if tools:
        kw["tools"] = tools
    if cfg.reasoning_effort:
        kw["reasoning_effort"] = cfg.reasoning_effort
    return kw
