-- Schema inicial — serviço de lançamentos (preenchido nas etapas de implementação)
CREATE TABLE IF NOT EXISTS schema_meta (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

INSERT INTO schema_meta (chave, valor)
VALUES ('service', 'lancamentos')
ON CONFLICT (chave) DO NOTHING;
