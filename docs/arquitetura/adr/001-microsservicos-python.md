# ADR-001 — Microsserviços em Python (FastAPI)

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O desafio exige dois serviços (lançamentos e consolidado) e deixa livre a linguagem. Também exige isolamento: lançamentos não podem cair junto com o consolidado.

## Decisão

Implementar **dois microsserviços HTTP** em **Python + FastAPI**, mais um frontend Python separado.

## Alternativas consideradas

| Alternativa | Prós | Contras |
|---|---|---|
| Monólito FastAPI com módulos | Deploy único | Isolamento de falha é artificial |
| .NET / Java / Node | Ecossistemas fortes | Fora da linguagem escolhida para o projeto |
| gRPC entre serviços | Contratos binários eficientes | Complexidade desnecessária para MVP HTTP + eventos |

## Consequências

- Contratos REST claros e documentados (OpenAPI).
- Deploys e escalas independentes.
- Overhead operacional maior que monólito (mitigado com Docker Compose no MVP).
