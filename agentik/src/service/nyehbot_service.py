import logging

from langchain.messages import HumanMessage

logger = logging.getLogger(__name__)


async def generate_answer(
    user_message: str,
    thread_id: str,
    agent,
) -> str:
    cleaned_message = user_message.strip()

    if not cleaned_message:
        raise ValueError("Message cannot be empty")

    result = await agent.ainvoke(
        {
            "messages": [
                HumanMessage(content=cleaned_message),
            ],
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            },
        },
    )

    last_message = result["messages"][-1]
    answer = str(last_message.content).lstrip('\n')
    usage = getattr(last_message, "usage_metadata", None) or {}

    logger.info(
        "thread=%s | agent=%s | user_message=%r | answer=%r | "
        "tokens(input=%s, output=%s, total=%s)",
        thread_id,
        result.get("route"),
        cleaned_message,
        answer,
        usage.get("input_tokens", "?"),
        usage.get("output_tokens", "?"),
        usage.get("total_tokens", "?"),
    )

    return answer