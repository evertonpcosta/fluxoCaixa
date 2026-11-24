import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SaldoDiarioModel(Base):
    __tablename__ = "saldo_diario"

    data_referencia: Mapped[date] = mapped_column(Date, primary_key=True)
    saldo: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EventoProcessadoModel(Base):
    __tablename__ = "eventos_processados"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    lancamento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    processado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
