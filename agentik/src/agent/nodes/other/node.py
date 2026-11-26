from src.agent.nodes.base import make_node

SYSTEM_PROMPT = """
You are Nyeh, a helpful assistant.

Answer clearly and accurately.
Keep responses concise unless the user asks for more detail.
""".strip()

ROUTE_DESCRIPTION = (
    "anything that is not about, does not mention, and is not directed at "
    "Hans / Hans Naufal / Hans Naufal Granito — general knowledge, unrelated "
    "topics, other people, small talk, or requests with no connection to "
    "that person"
)

call_other = make_node(SYSTEM_PROMPT)
