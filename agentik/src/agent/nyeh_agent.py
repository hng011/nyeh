from langchain.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from src.agent.nodes.me import node as me_agent
from src.agent.nodes.other import node as other_agent
from src.agent.state import AgentState, llm
from src.core.settings import settings

# ponytail: add a persona = add its package under src/agent/nodes/ (see
# nodes/other for the shape, incl. ROUTE_DESCRIPTION) and register it here.
# Everything below (prompt, edges, fallback) reads from this dict.
PERSONA_NODES = {
    "me_agent": me_agent.call_me,
    "other_agent": other_agent.call_other,
}
PERSONA_DESCRIPTIONS = {
    "me_agent": me_agent.ROUTE_DESCRIPTION,
    "other_agent": other_agent.ROUTE_DESCRIPTION,
}
ROUTES = tuple(PERSONA_NODES)
DEFAULT_ROUTE = ROUTES[0]


async def routing_agent(state: AgentState) -> dict:
    """Routing agent: decide which persona node should answer this turn."""

    options = "\n".join(f'"{name}" = {desc}' for name, desc in PERSONA_DESCRIPTIONS.items())
    prompt = (
        f"Classify the latest user message into exactly one of: {', '.join(ROUTES)}.\n"
        f"{options}\n"
        "Reply with only the single word."
    )

    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            *state["messages"][-settings.history_chat_window:],
        ]
    )

    route = str(response.content).strip().lower()

    return {
        "route": route if route in ROUTES else DEFAULT_ROUTE,
    }


def build_nyeh_agent(checkpointer: BaseCheckpointSaver):
    """Build and compile the Nyehbot LangGraph: router -> persona node."""

    builder = StateGraph(AgentState)

    builder.add_node("routing_agent", routing_agent)
    for name, node in PERSONA_NODES.items():
        builder.add_node(name, node)

    builder.add_edge(START, "routing_agent")
    builder.add_conditional_edges(
        "routing_agent",
        lambda state: state["route"],
        {name: name for name in PERSONA_NODES},
    )
    for name in PERSONA_NODES:
        builder.add_edge(name, END)

    return builder.compile(
        checkpointer=checkpointer,
    )
