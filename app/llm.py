import json
import os
import time

from openai import OpenAI
from pydantic import BaseModel

from app import config

PROVIDERS = {
    "crusoe": {"base_url": os.getenv("CRUSOE_BASE_URL", "https://api.inference.crusoecloud.com/v1"),
               "key_env": "CRUSOE_API_KEY", "model": os.getenv("CRUSOE_MODEL_EXTRACT", "openai/gpt-oss-120b")},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY",
                   "model": "openai/gpt-oss-120b"},
}
CALL_LOG: list[dict] = []


class LLMUnavailable(Exception):
    pass


def _formats(model_cls: type[BaseModel]):
    yield {"type": "json_schema", "json_schema": {"name": model_cls.__name__, "schema": model_cls.model_json_schema()}}
    yield {"type": "json_object"}
    yield None


def extract_json(system: str, user: str, model_cls: type[BaseModel]) -> BaseModel:
    for name in config.LLM_PROVIDERS:
        cfg = PROVIDERS.get(name)
        key = os.getenv(cfg["key_env"]) if cfg else None
        if not key:
            continue
        client = OpenAI(api_key=key, base_url=cfg["base_url"], timeout=20)
        for fmt in _formats(model_cls):
            t0 = time.time()
            try:
                kw = {"response_format": fmt} if fmt else {}
                r = client.chat.completions.create(model=cfg["model"], temperature=0, messages=[
                    {"role": "system", "content": system + " Reply with JSON only."},
                    {"role": "user", "content": user}], **kw)
                text = r.choices[0].message.content or ""
                text = text[text.find("{"): text.rfind("}") + 1]
                out = model_cls.model_validate(json.loads(text))
                CALL_LOG.append({"provider": name, "model": cfg["model"], "ok": True,
                                 "latency_ms": int((time.time() - t0) * 1000),
                                 "prompt_tokens": getattr(r.usage, "prompt_tokens", None),
                                 "completion_tokens": getattr(r.usage, "completion_tokens", None)})
                return out
            except Exception as e:  # noqa: BLE001 - any provider/format failure falls through to the next
                CALL_LOG.append({"provider": name, "model": cfg["model"], "ok": False, "error": str(e)[:200],
                                 "latency_ms": int((time.time() - t0) * 1000)})
    raise LLMUnavailable("no provider succeeded")
