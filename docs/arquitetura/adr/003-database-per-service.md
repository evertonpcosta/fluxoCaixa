# ADR-003 — Database per service (PostgreSQL ×2)

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

Compartilhar um único banco entre lançamentos e consolidado facilitaria joins, mas acoplaria schemas e falhas, enfraquecendo a separação de domínios.

## Decisão

- **PostgreSQL Lançamentos:** tabelas `lancamentos`, `outbox`.
- **PostgreSQL Consolidado:** tabelas `saldo_diario`, `eventos_processados`.
- Integração **somente** via eventos (nunca SQL cruzado).

## Alternativas consideradas

| Alternativa | Prós | Contras |
|---|---|---|
| DB compartilhado | Menos containers | Acoplamento forte |
| SQLite por serviço | Setup mínimo | Frágil sob carga concorrente |
| Um Postgres com dois schemas | Economia de container | Fronteira frágil (mesmo processo/servidor) |

## Consequências

- Autonomia de evolução de schema.
- Impossível consulta SQL “saldo + lançamentos” no banco — composição fica na aplicação/UI.
- Dois volumes/containers no Compose (custo operacional aceitável).
