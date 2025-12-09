"""
LLM client adapter.

Prefers Claude (Anthropic) if a claude_api_key is set; otherwise OpenAI.
Falls back to DummyLLM when no provider or SDK is available.

Claude Agent SDK support:
- Uses anthropic Agents API if available (per https://platform.claude.com/docs/en/agent-sdk/overview).
- Falls back to plain messages if Agents are unavailable.
"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LLMConfig:
    claude_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    model: str = "claude-3.5-sonnet"


class LLMClient:
    def ask(self, buddy_name: str, persona_prompt: str, user_text: str) -> str:
        raise NotImplementedError


class DummyLLM(LLMClient):
    """Fallback LLM that echoes with persona context."""

    def __init__(self, reason: str = "no provider configured") -> None:
        self.reason = reason

    def ask(self, buddy_name: str, persona_prompt: str, user_text: str) -> str:
        return (
            f"[stubbed reply from {buddy_name} ({self.reason})] "
            f"{persona_prompt[:60]}... User asked: {user_text}"
        )


class ClaudeClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        try:
            import anthropic  # type: ignore
        except ImportError:
            raise RuntimeError("anthropic SDK not installed. Install anthropic to use Claude.")
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        # Agent SDK availability check
        self.agent_api = getattr(self.client, "agents", None)
        self.agent_id = None

    def ask(self, buddy_name: str, persona_prompt: str, user_text: str) -> str:
        try:
            # Try Agent SDK first
            if self.agent_api:
                if not self.agent_id:
                    agent = self.agent_api.create(
                        name=buddy_name,
                        model=self.model,
                        instructions=persona_prompt,
                    )
                    self.agent_id = getattr(agent, "id", None)
                if self.agent_id:
                    # Agent SDK message call; signature may evolve—handle broadly.
                    msg = self.agent_api.messages.create(
                        agent_id=self.agent_id,
                        messages=[{"role": "user", "content": user_text}],
                        max_output_tokens=256,
                    )
                    content = getattr(msg, "content", None)
                    if content and isinstance(content, list) and hasattr(content[0], "text"):
                        return content[0].text
                    return str(msg)
            # Fallback to plain messages API
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                system=persona_prompt,
                messages=[
                    {"role": "user", "content": user_text},
                ],
            )
            return resp.content[0].text if getattr(resp, "content", None) else "[empty response]"
        except Exception as e:
            msg = str(e)
            billing_hint = ""
            if "credit balance is too low" in msg or "insufficient" in msg.lower():
                billing_hint = " (check Claude billing/credits)"
            model_hint = ""
            if "not_found" in msg or "model" in msg:
                model_hint = " (try claude-3-5-sonnet-20241022 or claude-3-5-haiku-20241022)"
            return f"[Claude error]{billing_hint}{model_hint} {msg}"


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise RuntimeError("openai SDK not installed. Install openai to use OpenAI models.")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def ask(self, buddy_name: str, persona_prompt: str, user_text: str) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": persona_prompt},
                    {"role": "user", "content": user_text},
                ],
                max_tokens=256,
            )
            choice = resp.choices[0]
            return choice.message.content if choice and choice.message else "[empty response]"
        except Exception as e:
            return f"[OpenAI error] {e}"


def build_client(cfg: Dict[str, str], model: str) -> LLMClient:
    """
    Build an LLM client based on available API keys and installed SDKs.
    Preference: Claude -> OpenAI -> Dummy.
    """
    claude_key = cfg.get("claude_api_key")
    if claude_key:
        try:
            return ClaudeClient(claude_key, model)
        except Exception as e:
            return DummyLLM(reason=str(e))

    openai_key = cfg.get("openai_api_key")
    if openai_key:
        try:
            return OpenAIClient(openai_key, model)
        except Exception as e:
            return DummyLLM(reason=str(e))

    return DummyLLM(reason="no API key set; set claude_api_key or openai_api_key via `aibuddies config set`")
