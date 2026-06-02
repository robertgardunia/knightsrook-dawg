from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASS: str
    POSTGRES_DB: str
    API_KEY: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
