import json
import logging
import threading
from urllib.parse import urlparse

import pika
from pika.exceptions import AMQPConnectionError, AMQPError

from app.config import settings
from app.db import SessionLocal
from app.domain import DomainError
from app.metrics import EVENTS_FAILED, EVENTS_PROCESSED
from app.service import aplicar_evento_payload

logger = logging.getLogger(__name__)


class LancamentoConsumer:
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
            target=self._run, name="lancamento-consumer", daemon=True
        )
        self._thread.start()
        logger.info("Consumer de lançamentos iniciado")

    def stop(self) -> None:
        self._stop.set()
        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except AMQPConnectionError:
            pass
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Consumer de lançamentos parado")

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._consume_forever()
            except Exception:  # noqa: BLE001
                logger.exception("Consumer reiniciando após erro")
                EVENTS_FAILED.inc()
                self._close()
                self._stop.wait(2)

    def _consume_forever(self) -> None:
        channel = self._ensure_channel()

        def on_message(ch, method, _properties, body: bytes) -> None:
            if self._stop.is_set():
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
            try:
                payload = json.loads(body.decode("utf-8"))
                db = SessionLocal()
                try:
                    applied = aplicar_evento_payload(db, payload)
                    if applied:
                        EVENTS_PROCESSED.inc()
                        logger.info(
                            "Evento %s aplicado no saldo", payload.get("event_id")
                        )
                    else:
                        logger.info(
                            "Evento %s já processado (idempotente)",
                            payload.get("event_id"),
                        )
                finally:
                    db.close()
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except DomainError:
                logger.exception("Payload inválido — descartando mensagem")
                EVENTS_FAILED.inc()
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                logger.exception("Falha ao processar mensagem — requeue")
                EVENTS_FAILED.inc()
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        channel.basic_qos(prefetch_count=20)
        channel.basic_consume(
            queue=settings.rabbitmq_queue,
            on_message_callback=on_message,
            auto_ack=False,
        )
        while not self._stop.is_set():
            self._connection.process_data_events(time_limit=1)

    def _ensure_channel(self):
        params = pika.URLParameters(settings.rabbitmq_url)
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
        self._channel.queue_declare(queue=settings.rabbitmq_queue, durable=True)
        self._channel.queue_bind(
            queue=settings.rabbitmq_queue,
            exchange=settings.rabbitmq_exchange,
            routing_key=settings.rabbitmq_routing_key,
        )
        return self._channel

    def _close(self) -> None:
        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except (AMQPConnectionError, AMQPError):
            pass
        self._connection = None
        self._channel = None


consumer = LancamentoConsumer()
