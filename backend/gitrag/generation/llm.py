from __future__ import annotations

import ollama

from gitrag.core.exceptions import LLMUnavailableError
from gitrag.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    Thin wrapper around the Ollama Python client.
    All LLM calls go through here so error handling and logging are centralised.
    """

    def __init__(self, settings) -> None:
        self.model  = settings.llm_model
        self.cfg    = settings.generation
        self.host   = settings.ollama_host
        self._client = ollama.Client(host=self.host)

    def generate(self, messages: list[dict]) -> str:
        """Send messages to the local LLM and return the response text."""
        logger.debug(
            "llm_request",
            model      = self.model,
            max_tokens = self.cfg.max_tokens,
            temperature= self.cfg.temperature,
        )
        try:
            response = self._client.chat(
                model    = self.model,
                messages = messages,
                options  = {
                    "num_predict": self.cfg.max_tokens,
                    "temperature": self.cfg.temperature,
                },
            )
            content = response["message"]["content"]
            logger.debug("llm_response_received", length=len(content))
            return content

        except Exception as exc:
            logger.error("llm_error", error=str(exc), model=self.model)
            raise LLMUnavailableError(
                f"Ollama error — is it running at {self.host}?\n"
                f"Try: docker exec gitrag_ollama ollama pull {self.model}\n"
                f"Original error: {exc}"
            ) from exc

    def is_available(self) -> bool:
        """Return True if Ollama is reachable and the model is pulled."""
        try:
            models = self._client.list()
            names  = [m["name"] for m in models.get("models", [])]
            return any(self.model in name for name in names)
        except Exception:
            return False
