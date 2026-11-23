import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EventoProcessado(Base):
    __tablename__ = "eventos_processados"

    evento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    processado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SaldoDiario(Base):
    __tablename__ = "saldos_diarios"

    comerciante_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    data: Mapped[date] = mapped_column(Date, primary_key=True)
    total_creditos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_debitos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    saldo: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
