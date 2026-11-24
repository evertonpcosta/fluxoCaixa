CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS saldo_diario (
    data_referencia DATE PRIMARY KEY,
    saldo NUMERIC(18, 2) NOT NULL DEFAULT 0,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eventos_processados (
    event_id UUID PRIMARY KEY,
    lancamento_id UUID NOT NULL,
    processado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
