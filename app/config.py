from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVER_ADDRESS: str
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DATABASE: str
    POSTGRES_DRIVER: str
    POSTGRES_JDBC_URL: str
    POSTGRES_CONN: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

print(settings.POSTGRES_CONN)
