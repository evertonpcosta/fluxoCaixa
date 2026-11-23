import logging
import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.models import Base

logger = logging.getLogger(__name__)

engine = None
SessionLocal = None


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não configurada")
    return url


def init_db() -> None:
    global engine, SessionLocal
    engine = create_engine(database_url(), pool_pre_ping=True, pool_size=5, max_overflow=10)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    ultimo_erro: Exception | None = None
    for tentativa in range(1, 31):
        try:
            with engine.connect() as conexao:
                conexao.execute(text("SELECT 1"))
            Base.metadata.create_all(engine)
            logger.info("banco de lançamentos pronto")
            return
        except OperationalError as exc:
            ultimo_erro = exc
            logger.warning("banco indisponível, tentativa %s/30", tentativa)
            time.sleep(1)
    raise RuntimeError("não foi possível conectar ao banco de lançamentos") from ultimo_erro
