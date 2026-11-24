import json
import logging
import threading
from urllib.parse import urlparse

import pika
from pika.exceptions import (
    AMQPConnectionError,
    AMQPError,
    NackError,
    UnroutableError,
)

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
    """Relay do outbox → RabbitMQ com topologia provisionada e publisher confirms."""

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
                try:
                    # confirm_delivery() faz basic_publish bloquear até ack do broker
                    # (ou levantar NackError/UnroutableError).
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
                        mandatory=True,
                    )
                except (NackError, UnroutableError):
                    PUBLISH_FAILURES.inc()
                    logger.exception(
                        "Broker não confirmou evento %s — permanece no outbox",
                        item.event_id,
                    )
                    self._close()
                    return

                marcar_outbox_publicado(db, item.id)
                logger.info("Evento %s publicado e confirmado pelo broker", item.event_id)

            OUTBOX_PENDING.set(contar_outbox_pendentes(db))
        finally:
            db.close()

    def _ensure_channel(self):
        if self._connection and self._connection.is_open and self._channel:
            return self._channel

        params = pika.URLParameters(settings.rabbitmq_url)
        parsed = urlparse(settings.rabbitmq_url)
        if not parsed.path or parsed.path == "/":
            params.virtual_host = "/"

        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._declare_topology(self._channel)
        # Exige confirmação do broker antes de considerar a publicação ok
        self._channel.confirm_delivery()
        return self._channel

    def _declare_topology(self, channel) -> None:
        """Exchange + fila + bind no publisher: mensagem não some se o consolidado ainda não subiu."""
        channel.exchange_declare(
            exchange=settings.rabbitmq_exchange,
            exchange_type="topic",
            durable=True,
        )
        channel.queue_declare(queue=settings.rabbitmq_queue, durable=True)
        channel.queue_bind(
            queue=settings.rabbitmq_queue,
            exchange=settings.rabbitmq_exchange,
            routing_key=settings.rabbitmq_routing_key,
        )

    def _close(self) -> None:
        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except (AMQPConnectionError, AMQPError):
            pass
        self._connection = None
        self._channel = None


publisher = OutboxPublisher()
