"""Model profiles: the only place that knows which LLM is driving.

The agent loop sees a LangChain chat model plus a ``ModelProfile``. Adding a model
means adding a profile here; nothing else changes.

``context_window`` is the budget the loop works within, which can be smaller than
what the model supports: for the local server it's the server's ``-c`` setting
(see ~/otherPeoplesCode/llama.cpp/run-vision-server.sh), and for paid models it
caps cost per call.

Paid (OpenRouter) profiles are defined but never run without an explicit
``--allow-paid``; see gb_agent/play.py.
"""

from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel

LOCAL_SERVER = "http://127.0.0.1:8080/v1"


@dataclass(frozen=True)
class ModelProfile:
    name: str  # label used in logs and run metadata
    provider: str  # "local" (llama-server) or "openrouter"
    model: str  # model id at that provider
    context_window: int  # tokens; when the context nears this, it's compacted
    vision: bool  # can it take screenshots as images?
    base_url: str | None = None  # for local
    temperature: float = 0.7
    max_output_tokens: int = 1024
    images_per_step: int = 2  # screenshots shown after each step (before, after)
    describer: str | None = None  # without vision: profile that describes screens

    @property
    def paid(self) -> bool:
        return self.provider != "local"


PROFILES: dict[str, ModelProfile] = {p.name: p for p in [
    ModelProfile(
        name="qwen3-vl-2b-local",
        provider="local",
        model="qwen3-vl-2b",  # llama-server's --alias
        base_url=LOCAL_SERVER,
        context_window=16_384,
        vision=True,
    ),
    ModelProfile(
        name="qwen3-vl-8b",
        provider="openrouter",
        model="qwen/qwen3-vl-8b-instruct",
        context_window=64_000,
        vision=True,
        max_output_tokens=2048,
    ),
    ModelProfile(
        name="claude-haiku-5.5",
        provider="openrouter",
        model="anthropic/claude-haiku-5.5",
        context_window=64_000,
        vision=True,
        max_output_tokens=2048,
    ),
]}


def get_profile(name: str) -> ModelProfile:
    try:
        return PROFILES[name]
    except KeyError:
        raise ValueError(f"no model profile {name!r}; known: {', '.join(PROFILES)}") from None


def build_chat_model(profile: ModelProfile) -> BaseChatModel:
    if profile.provider == "local":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=profile.model,
            base_url=profile.base_url,
            api_key="not-needed",
            temperature=profile.temperature,
            max_tokens=profile.max_output_tokens,
            timeout=1_800,  # a full 16k context takes minutes on this CPU
            max_retries=0,  # the agent loop retries
        )
    if profile.provider == "openrouter":
        from agents.config import get_llm  # imports GCP secrets; only when needed

        return get_llm(profile.model, temperature=profile.temperature)
    raise ValueError(f"unknown provider {profile.provider!r}")
