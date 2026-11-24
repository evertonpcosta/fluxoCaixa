# Checklist de entrega — Desafio Arquiteto de Soluções

Conferência dos requisitos do PDF `desafio-arquiteto-solucao-jun25`.

## Requisitos de negócio

| Requisito | Status | Onde |
|---|---|---|
| Serviço de controle de lançamentos | Atendido | `services/lancamentos` |
| Serviço do consolidado diário | Atendido | `services/consolidado` |

## Requisitos obrigatórios

| Requisito | Status | Onde |
|---|---|---|
| Mapeamento de domínios e capacidades | Atendido | `docs/arquitetura/dominios-e-capacidades.md` |
| Refinamento RF / RNF | Atendido | `docs/arquitetura/requisitos.md` |
| Desenho da solução (Arquitetura Alvo) | Atendido | `docs/arquitetura/arquitetura-alvo.md` + `docs/diagramas/` |
| Justificativa de tecnologias / tipo de arquitetura | Atendido | Arquitetura alvo + ADRs |
| Implementação na linguagem dominada | Atendido | Python (FastAPI + Streamlit) |
| Testes | Atendido | `services/*/tests` + `scripts/` |
| README com como funciona e como rodar | Atendido | `README.md` |
| Repositório público no GitHub | Atendido | remote configurado |
| Documentações no repositório | Atendido | `docs/` |

## Requisitos não funcionais

| Requisito | Status | Evidência |
|---|---|---|
| Lançamentos não caem se consolidado cair | Atendido | Outbox + fila; `scripts/isolamento_consolidado.py` |
| Eventos recuperáveis / partida com consolidado down | Atendido | Publisher confirma + declara fila; `scripts/partida_consolidado_down.py` |
| Consolidado ~50 rps, perda ≤ 5% **e** vazão | Atendido (script) | `scripts/carga_consolidado.py` (perda + RPS mínimo) |

## Diferenciais

| Item | Status | Onde |
|---|---|---|
| Arquitetura de transição | Atendido (conceitual) | `arquitetura-alvo.md` |
| Estimativa de custos | Atendido | `custos.md` |
| Monitoramento e observabilidade | Atendido | Prometheus + Grafana no Compose |
| Critérios de segurança de consumo | Atendido | `seguranca.md` |
| Evoluções futuras | Atendido | `evolucoes-futuras.md` |

## Smoke local rápido

```bash
docker compose up -d --build
curl -s http://localhost:8001/health
curl -s http://localhost:8002/health
curl -s -X POST http://localhost:8001/lancamentos \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"CREDITO","valor":"10.00","descricao":"smoke","data_lancamento":"2026-11-24"}'
sleep 2
curl -s 'http://localhost:8002/saldo?data=2026-11-24'
```
