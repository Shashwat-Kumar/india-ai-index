"""Pluggable providers. Each reads its API key from an env var; none is bundled."""
from __future__ import annotations
import os, time
from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    latency_s: float


class Provider:
    name = "base"
    env_key = ""
    # USD per 1M tokens; set via config at run time (prices change, so none are hard-coded as fact)
    def __init__(self, model: str, price_in_usd_per_m: float = 0.0, price_out_usd_per_m: float = 0.0):
        self.model, self.pin, self.pout = model, price_in_usd_per_m, price_out_usd_per_m

    @property
    def key(self):
        return os.getenv(self.env_key, "")

    def available(self) -> bool:
        return bool(self.key)

    def complete(self, prompt: str) -> Completion:  # pragma: no cover
        raise NotImplementedError

    def _timed(self, fn: Callable[[], tuple]) -> Completion:
        t = time.time(); text, i, o = fn()
        return Completion(text, i, o, time.time() - t)


class OpenAICompatible(Provider):
    """OpenAI, xAI and Sarvam-style OpenAI-compatible endpoints."""
    name, env_key, base_url = "openai", "OPENAI_API_KEY", None

    def complete(self, prompt):
        from openai import OpenAI
        c = OpenAI(api_key=self.key, base_url=self.base_url)
        def f():
            r = c.chat.completions.create(model=self.model, temperature=0, messages=[{"role": "user", "content": prompt}])
            return r.choices[0].message.content or "", r.usage.prompt_tokens, r.usage.completion_tokens
        return self._timed(f)


class XAI(OpenAICompatible):
    name, env_key, base_url = "xai", "XAI_API_KEY", "https://api.x.ai/v1"


class Sarvam(OpenAICompatible):
    name, env_key = "sarvam", "SARVAM_API_KEY"
    base_url = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai/v1")


class Anthropic(Provider):
    name, env_key = "anthropic", "ANTHROPIC_API_KEY"
    def complete(self, prompt):
        import anthropic
        c = anthropic.Anthropic(api_key=self.key)
        def f():
            r = c.messages.create(model=self.model, max_tokens=1024, temperature=0, messages=[{"role": "user", "content": prompt}])
            return "".join(b.text for b in r.content if hasattr(b, "text")), r.usage.input_tokens, r.usage.output_tokens
        return self._timed(f)


class Google(Provider):
    name, env_key = "google", "GOOGLE_API_KEY"
    def complete(self, prompt):
        from google import genai
        c = genai.Client(api_key=self.key)
        def f():
            r = c.models.generate_content(model=self.model, contents=prompt)
            u = r.usage_metadata
            return r.text or "", u.prompt_token_count or 0, u.candidates_token_count or 0
        return self._timed(f)


class HuggingFace(Provider):
    name, env_key = "hf", "HF_TOKEN"
    def complete(self, prompt):
        from huggingface_hub import InferenceClient
        c = InferenceClient(model=self.model, token=self.key)
        def f():
            r = c.chat_completion(messages=[{"role": "user", "content": prompt}], max_tokens=1024, temperature=0.01)
            u = getattr(r, "usage", None)
            return r.choices[0].message.content, getattr(u, "prompt_tokens", 0), getattr(u, "completion_tokens", 0)
        return self._timed(f)


class Mock(Provider):
    """Deterministic offline provider for tests. Returns the reference answer when `oracle` is set."""
    name, env_key = "mock", ""
    def __init__(self, model="mock-1", oracle: Dict[str, str] | None = None, **kw):
        super().__init__(model, **kw); self.oracle = oracle or {}
    def available(self): return True
    def complete(self, prompt):
        for k, v in self.oracle.items():
            if k in prompt:
                return Completion(v, len(prompt) // 4, len(v) // 4, 0.0)
        return Completion("I don't know", len(prompt) // 4, 3, 0.0)


REGISTRY = {c.name: c for c in (OpenAICompatible, XAI, Sarvam, Anthropic, Google, HuggingFace, Mock)}
