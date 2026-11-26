from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState

from src.core.settings import settings


class AgentState(MessagesState):
    route: str


llm = init_chat_model(
    model=settings.llm_model_name,
    model_provider="openai",
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    temperature=settings.temperature,
)
