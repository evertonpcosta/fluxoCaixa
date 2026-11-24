import json
import logging
import threading
import time
from urllib.parse import urlparse

import pika
from pika.exceptions import AMQPConnectionError

from app.config import settings
from app.db import SessionLocal
from app.metrics import OUTBOX_PENDING, PUBLISH_FAILURES
from app.repository import (
    contar_outbox_pendentes,
    listar_outbox_pendentes,
    marcar_outbox_publicado,
)

logger = logging.getLogger(__name__)


class OutboxPublisher:
    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._connection: pika.BlockingConnection | None = None
        self._channel = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="outbox-publisher", daemon=True
        )
        self._thread.start()
        logger.info("Outbox publisher iniciado")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._close()
        logger.info("Outbox publisher parado")

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._publish_batch()
            except Exception:  # noqa: BLE001
                logger.exception("Erro no ciclo do outbox publisher")
                PUBLISH_FAILURES.inc()
                self._close()
            self._stop.wait(settings.outbox_poll_seconds)

    def _publish_batch(self) -> None:
        db = SessionLocal()
        try:
            pending = contar_outbox_pendentes(db)
            OUTBOX_PENDING.set(pending)
            if pending == 0:
                return

            channel = self._ensure_channel()
            for item in listar_outbox_pendentes(db):
                body = json.dumps(item.payload, ensure_ascii=True).encode("utf-8")
                channel.basic_publish(
                    exchange=settings.rabbitmq_exchange,
                    routing_key=settings.rabbitmq_routing_key,
                    body=body,
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=2,
                        message_id=str(item.event_id),
                        type=item.event_type,
                    ),
                )
                marcar_outbox_publicado(db, item.id)
                logger.info("Evento %s publicado", item.event_id)

            OUTBOX_PENDING.set(contar_outbox_pendentes(db))
        finally:
            db.close()

    def _ensure_channel(self):
        if self._connection and self._connection.is_open and self._channel:
            return self._channel

        params = pika.URLParameters(settings.rabbitmq_url)
        # Garante virtual host padrão se a URL não trouxer path
        parsed = urlparse(settings.rabbitmq_url)
        if not parsed.path or parsed.path == "/":
            params.virtual_host = "/"

        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(
            exchange=settings.rabbitmq_exchange,
            exchange_type="topic",
            durable=True,
        )
        return self._channel

    def _close(self) -> None:
        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except AMQPConnectionError:
            pass
        self._connection = None
        self._channel = None


publisher = OutboxPublisher()
