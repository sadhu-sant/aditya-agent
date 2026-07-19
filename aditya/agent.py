"""
Aditya's core agent loop.

Provider-agnostic: LiteLLM lets the exact same code call OpenAI, Anthropic,
Groq, Gemini, Mistral, local Ollama models, and 100+ others. Swap providers
by changing ADITYA_MODEL (and the matching *_API_KEY) — no code changes.
"""
import json
import logging

import litellm

from .config import settings
from .tools import TOOL_REGISTRY, TOOL_SCHEMAS

logger = logging.getLogger("aditya")


class Aditya:
    def __init__(
        self,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        use_tools: bool = True,
    ):
        self.model = model or settings.MODEL
        self.system_prompt = system_prompt or settings.SYSTEM_PROMPT
        self.temperature = settings.TEMPERATURE if temperature is None else temperature
        self.max_tokens = max_tokens or settings.MAX_TOKENS
        self.use_tools = use_tools

    def _call_model(self, messages: list[dict]) -> "litellm.ModelResponse":
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if self.use_tools:
            kwargs["tools"] = TOOL_SCHEMAS
            kwargs["tool_choice"] = "auto"
        return litellm.completion(**kwargs)

    def run(self, history: list[dict], user_message: str) -> tuple[str, list[dict]]:
        """
        Run one turn of the agent: append the user's message, let the model
        think and optionally call tools (looping until it produces a final
        answer or hits MAX_TOOL_ITERATIONS), and return (reply, new_history).
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        messages += history
        messages.append({"role": "user", "content": user_message})

        for _ in range(settings.MAX_TOOL_ITERATIONS):
            response = self._call_model(messages)
            choice = response.choices[0]
            msg = choice.message

            tool_calls = getattr(msg, "tool_calls", None)
            if not tool_calls:
                # Final answer
                reply = msg.content or ""
                messages.append({"role": "assistant", "content": reply})
                # Strip the system prompt before returning history to the caller
                return reply, messages[1:]

            # Model wants to use one or more tools — execute them all, then loop
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [tc.model_dump() for tc in tool_calls],
                }
            )
            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                fn = TOOL_REGISTRY.get(fn_name)
                if fn is None:
                    result = f"Unknown tool: {fn_name}"
                else:
                    try:
                        result = fn(**args)
                    except Exception as e:
                        result = f"Tool '{fn_name}' raised an error: {e}"

                logger.info("tool=%s args=%s", fn_name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": str(result),
                    }
                )

        # Safety valve: too many tool iterations
        fallback = "I wasn't able to finish that within my tool-call budget — could you narrow the request?"
        messages.append({"role": "assistant", "content": fallback})
        return fallback, messages[1:]
