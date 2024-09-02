from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    max_session_connect_delay: int = 60  # Default value of 60 seconds
    SLEEP_BETWEEN_CLAIM: list[int] = [10, 20]
    SLEEP_BETWEEN_TASK_CLAIM: list[int] = [5, 10]
    SLEEP_BETWEEN_FARMING: list[int] = [10, 20]

    USE_PROXY_FROM_FILE: bool = True


settings = Settings()
