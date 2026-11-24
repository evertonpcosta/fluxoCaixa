CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS lancamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('CREDITO', 'DEBITO')),
    valor NUMERIC(18, 2) NOT NULL CHECK (valor > 0),
    descricao VARCHAR(255) NOT NULL DEFAULT '',
    data_lancamento DATE NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos (data_lancamento);

CREATE TABLE IF NOT EXISTS outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    publicado_em TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_outbox_pendentes
    ON outbox (criado_em)
    WHERE publicado_em IS NULL;
