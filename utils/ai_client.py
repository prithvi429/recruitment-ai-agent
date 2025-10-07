"""Simple AI client wrapper for OpenAI with safe fallbacks.

This module provides AIClient which wraps chat completions and embeddings
with basic retry/backoff and a deterministic local fallback when no
OPENAI_API_KEY is configured. The code is small, well-documented and
dependency-light so it fits into the existing project.

Usage:
    from utils.ai_client import AIClient

    client = AIClient()  # reads OPENAI_API_KEY from environment if set
    resp = client.chat("Summarize: ...")
    emb = client.embed("some text")

The implementation intentionally avoids heavy assumptions about models and
keeps behaviour predictable when the API key is missing (useful for local
testing).
"""
from __future__ import annotations

import os
import time
import random
from typing import Any, Dict, List, Optional, Sequence, Union

try:
    # optional dependency; project requirements include openai
    import openai
    from openai.error import APIError, RateLimitError, ServiceUnavailableError
except Exception:  # pragma: no cover - fallback when openai isn't installed
    openai = None  # type: ignore
    APIError = RateLimitError = ServiceUnavailableError = Exception  # type: ignore

from dotenv import load_dotenv

load_dotenv()


class AIClient:
    """A small wrapper around OpenAI API with retries and a local fallback.

    Contract:
    - chat(prompt|messages) -> str text response
    - embed(text) -> List[float] embedding vector

    Inputs: strings or chat-style messages. Outputs: plain text or list of floats.
    Error modes: raises RuntimeError for unrecoverable failures. When no
    OpenAI API key is present, deterministic local fallbacks are used.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-3.5-turbo",
        embedding_model: str = "text-embedding-3-small",
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.default_model = default_model
        self.embedding_model = embedding_model
        self.timeout = timeout

        if openai is not None and self.api_key:
            openai.api_key = self.api_key

    def _has_openai(self) -> bool:
        return openai is not None and bool(self.api_key)

    def chat(
        self,
        prompt_or_messages: Union[str, Sequence[Dict[str, str]]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
    ) -> str:
        """Return a text response for the given prompt or message list.

        Accepts either a single string prompt or a list of chat messages in
        OpenAI format: [{"role": "user", "content": "..."}, ...].
        """
        model = model or self.default_model

        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        else:
            messages = list(prompt_or_messages)

        if not messages:
            return ""

        if not self._has_openai():
            return self._local_chat_stub(messages)

        attempt = 0
        while True:
            try:
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    request_timeout=self.timeout,
                )
                # follow standard structure: choices[0].message.content
                content = resp.choices[0].message.get("content")
                if content is None:
                    # some responses might only have 'text' depending on version
                    content = getattr(resp.choices[0], "text", "")
                return content.strip()

            except (RateLimitError, ServiceUnavailableError, APIError) as exc:
                attempt += 1
                if attempt > max_retries:
                    raise RuntimeError(f"OpenAI request failed after retries: {exc}")
                sleep = retry_backoff * (2 ** (attempt - 1)) + random.random() * 0.1
                time.sleep(sleep)

            except Exception as exc:  # pragma: no cover - unexpected
                raise RuntimeError(f"Unexpected OpenAI error: {exc}")

    def embed(self, text: str, *, model: Optional[str] = None) -> List[float]:
        """Return an embedding vector for `text`.

        If OpenAI isn't available, produce a deterministic pseudo-embedding
        (useful for local tests).
        """
        if not text:
            return []

        model = model or self.embedding_model

        if not self._has_openai():
            return self._local_embed_stub(text)

        attempt = 0
        max_retries = 3
        while True:
            try:
                resp = openai.Embedding.create(input=[text], model=model)
                emb = resp.data[0].embedding
                return list(emb)

            except (RateLimitError, ServiceUnavailableError, APIError) as exc:
                attempt += 1
                if attempt > max_retries:
                    raise RuntimeError(f"Embedding request failed after retries: {exc}")
                time.sleep(0.5 * (2 ** (attempt - 1)))

            except Exception as exc:  # pragma: no cover - unexpected
                raise RuntimeError(f"Unexpected OpenAI error: {exc}")

    # --- Local fallback implementations ---
    def _local_chat_stub(self, messages: Sequence[Dict[str, str]]) -> str:
        """Deterministic fallback chat response when no API key is configured.

        Keeps the reply short and stable for a given input for easier tests.
        """
        # join user messages to form a small deterministic summary
        joined = " \n ".join(m.get("content", "") for m in messages)
        # create a short pseudo-summary
        excerpt = joined.strip()[:500]
        return f"[local-fallback] received {len(joined)} chars; echo: {excerpt}"

    def _local_embed_stub(self, text: str, dim: int = 1536) -> List[float]:
        """Return a deterministic pseudo-embedding for `text`.

        We hash the input and expand it to a float vector in [-1,1]. This
        is not a real embedding. Keep `dim` reasonably large to mimic real
        embedding sizes.
        """
        # keep deterministic across runs
        seed = 0
        for ch in text:
            seed = (seed * 1315423911) ^ ord(ch)
        rnd = random.Random(seed & 0xFFFFFFFF)
        # smaller dim to keep returned size reasonable if the real model is absent
        dim = min(dim, 512)
        return [rnd.uniform(-1.0, 1.0) for _ in range(dim)]


__all__ = ["AIClient"]
