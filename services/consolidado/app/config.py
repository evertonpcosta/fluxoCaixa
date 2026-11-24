from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://fluxo:fluxo@localhost:5432/consolidado"
    rabbitmq_url: str = "amqp://fluxo:fluxo@localhost:5672/"
    rabbitmq_exchange: str = "fluxo.caixa"
    rabbitmq_routing_key: str = "lancamento.criado"
    rabbitmq_queue: str = "consolidado.lancamento.criado"
    log_level: str = "INFO"


settings = Settings()
