from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://fluxo:fluxo@localhost:5432/lancamentos"
    rabbitmq_url: str = "amqp://fluxo:fluxo@localhost:5672/"
    rabbitmq_exchange: str = "fluxo.caixa"
    rabbitmq_routing_key: str = "lancamento.criado"
    rabbitmq_queue: str = "consolidado.lancamento.criado"
    outbox_poll_seconds: float = 1.0
    log_level: str = "INFO"


settings = Settings()
