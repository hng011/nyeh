from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# LangSmith's SDK reads LANGSMITH_* directly from the process env, so
# these need to actually land in os.environ, not just in this Settings object.
load_dotenv()


class Settings(BaseSettings):
    # Application
    environment: str = Field(alias="ENVIRONMENT")
    app_name: str = Field(alias="APP_NAME")
    app_version: str = Field(alias="APP_VERSION")

    cors_origins: list[str] = Field(default=['*'], alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list[str] = Field(default=['*'], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: list[str] = Field(default=['*'], alias="CORS_ALLOW_HEADERS")

    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_model_name: str = Field(alias="LLM_MODEL_NAME")
    history_chat_window: int = Field(alias="HISTORY_CHAT_WINDOW")
    temperature: float = Field(default=0.8, alias="TEMPERATURE")
    top_k: int = Field(default=10, alias="TOP_K")

    api_secret_key: str = Field(alias="API_SECRET_KEY")
    session_secret_key: str = Field(alias="SESSION_SECRET_KEY")
    session_token_ttl: int = Field(alias="SESSION_TOKEN_TTL")  # seconds, matches WS idle timeout

    ws_max_msg_size: int = Field(alias="WS_MAX_MSG_SIZE")
    ws_rate_limit: int = Field(alias="WS_RATE_LIMIT")
    ws_rate_window: int = Field(alias="WS_RATE_WINDOW")  # seconds
    ws_idle_timeout: int = Field(alias="WS_IDLE_TIMEOUT")  # seconds
    ws_max_connections_per_key: int = Field(alias="WS_MAX_CONNECTIONS_PER_KEY")
    # Per client IP, across all connections/tokens: caps LLM spend per visitor.
    ip_rate_limit: int = Field(default=30, alias="IP_RATE_LIMIT")
    ip_rate_window: int = Field(default=600, alias="IP_RATE_WINDOW")  # seconds

    qdrant_endpoint: str = Field(alias="QDRANT_ENDPOINT")
    qdrant_api_key: str = Field(alias="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(alias="QDRANT_COLLECTION_NAME")

    data_dir: str = Field(default="./data", alias="DATA_DIR")


    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()