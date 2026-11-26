import json
import logging
from pathlib import Path
from typing import Awaitable, Callable

from langchain.messages import SystemMessage, HumanMessage
from langchain_core.messages import convert_to_openai_messages

from src.agent.state import AgentState, llm
from src.core.settings import settings

logger = logging.getLogger(__name__)

FINETUNE_LOG = Path(settings.data_dir) / "finetune.jsonl"


def log_finetune_example(messages: list) -> None:
    """Append one OpenAI chat fine-tuning example: exactly what the LLM saw + its answer."""
    try:
        with FINETUNE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"messages": convert_to_openai_messages(messages)}, ensure_ascii=False) + "\n")
    except Exception:
        # Dataset capture must never break a live chat.
        logger.exception("failed to write fine-tune example")


def make_node(system_prompt: str, retrieve: Callable[[str], Awaitable[str]] | None = None):
    """Build a persona node: system prompt + recent history -> one LLM call.

    `retrieve`, if given, is called with the latest user message and its
    return value (already formatted, e.g. wrapped in its own tags) is
    appended to the system prompt before the LLM call — this is the only
    hook a persona needs to bolt on its own RAG without touching other
    personas.
    """

    async def call(state: AgentState) -> dict:
        latest_user_message = str(state["messages"][-1].content)
        
        messages = [
            SystemMessage(content=system_prompt),
            *state["messages"][-settings.history_chat_window:],
        ]
        
        if retrieve is not None:
            context = await retrieve(latest_user_message)

            messages[-1] = HumanMessage(
                content=f"""
                    {context}

                    <user_question>
                    {latest_user_message}
                    </user_question>
                """
            )

        logger.info("prompt sent to llm:\n%s", messages)

        response = await llm.ainvoke(messages)
        log_finetune_example([*messages, response])
        return {"messages": [response]}

    return call
