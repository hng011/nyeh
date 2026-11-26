import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel

from src.core.settings import settings
from src.api.v1.endpoints import router
from src.websocket.nyehbot_websocket import ws_router
from src.agent.nyeh_agent import build_nyeh_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(api: FastAPI):
    # Chat history survives restarts; DATA_DIR is the pod's persistent volume.
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(f"{settings.data_dir}/checkpoints.sqlite") as checkpointer:
        api.state.nyeh_agent = build_nyeh_agent(checkpointer)
        api.state.nyeh_agent_graph_png = api.state.nyeh_agent.get_graph().draw_png()

        yield


api = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Configure CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

api.include_router(router=router, prefix="/api")
api.include_router(router=ws_router, prefix="/ws_api")


class GetIndex(BaseModel):
    api_title: str
    api_version: str
    api_description: str
    status_code: int 
    
@api.get("/")
async def index():
    return GetIndex(
        api_title=api.title,
        api_version=api.version,
        api_description=api.description,
        status_code=status.HTTP_200_OK,
    )