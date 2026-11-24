# FluxoCaixa

Sistema de **fluxo de caixa diário** para um comerciante: registrar lançamentos (crédito/débito) e consultar o **saldo consolidado do dia**.

Desafio de Arquiteto de Soluções — stack **100% Python**, com microsserviços desacoplados por mensageria e observabilidade (**Prometheus + Grafana**).

## Como funciona

```text
Comerciante (Streamlit)
        │
        ├── POST/GET ──► API Lançamentos (FastAPI) ──► PostgreSQL + Outbox
        │                        │
        │                        └── publish ──► RabbitMQ
        │                                           │
        └── GET /saldo ──► API Consolidado (FastAPI) ◄── consumer idempotente
                                   │
                                   └── PostgreSQL (saldo_diario)
```

Pontos-chave:

- **Isolamento (NFR):** se o consolidado cair, lançamentos continuam aceitando requests (outbox + fila).
- **Consistência eventual:** o saldo pode atrasar segundos após o lançamento.
- **Observabilidade:** métricas em `/metrics`, dashboards no Grafana.

Documentação completa: [`docs/arquitetura/`](docs/arquitetura/) · Diagramas: [`docs/diagramas/`](docs/diagramas/) · Checklist: [`docs/arquitetura/checklist-entrega.md`](docs/arquitetura/checklist-entrega.md)

## Pré-requisitos

- Docker + Docker Compose
- (Opcional) Python 3.12+ para rodar testes/scripts fora do container

## Subir a stack

```bash
docker compose up -d --build
```

| Serviço | URL / porta | Credenciais |
|---|---|---|
| Frontend Streamlit | http://localhost:8501 | — |
| API Lançamentos | http://localhost:8001 | — |
| API Consolidado | http://localhost:8002 | — |
| RabbitMQ Management | http://localhost:15672 | `fluxo` / `fluxo` |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | `admin` / `admin` |

Parar / limpar:

```bash
docker compose down
# com volumes:
docker compose down -v
```

Logs:

```bash
docker compose logs -f lancamentos consolidado
```

## Uso rápido (API)

```bash
# criar lançamento
curl -s -X POST http://localhost:8001/lancamentos \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"CREDITO","valor":"100.00","descricao":"venda","data_lancamento":"2026-11-24"}'

# listar
curl -s 'http://localhost:8001/lancamentos?data=2026-11-24'

# saldo (aguarde ~1–2s após o POST)
curl -s 'http://localhost:8002/saldo?data=2026-11-24'
```

OpenAPI:

- http://localhost:8001/docs
- http://localhost:8002/docs

## Frontend

http://localhost:8501

- Novo lançamento
- Listagem (filtro por data)
- Saldo diário
- Se consolidado estiver DOWN, a UI avisa e **não bloqueia** novos lançamentos

## Testes

```bash
# unitários — lançamentos
cd services/lancamentos && pip install -r requirements.txt && PYTHONPATH=. pytest -q

# unitários — consolidado
cd services/consolidado && pip install -r requirements.txt && PYTHONPATH=. pytest -q
```

## Evidências NFR

```bash
pip install -r scripts/requirements.txt
bash scripts/run_all.sh
```

| Script | Critério |
|---|---|
| `isolamento_consolidado.py` | Lançamentos UP com consolidado DOWN |
| `carga_consolidado.py` | ~50 rps, perda ≤ 5% |
| `atraso_saldo.py` | Lag evento → saldo |
| `recuperacao_outbox.py` | Drain após recover |

Resultados: [`docs/resultados/`](docs/resultados/)

## Estrutura do repositório

```text
fluxoCaixa/
├── docker-compose.yaml
├── docs/                 # arquitetura, diagramas C4, evidências
├── frontend/             # Streamlit
├── services/
│   ├── lancamentos/      # FastAPI + outbox publisher
│   └── consolidado/      # FastAPI + consumer
├── infra/                # Postgres, RabbitMQ, Prometheus, Grafana
└── scripts/              # isolamento, carga, recuperação
```

## Decisões principais

| Decisão | Motivo |
|---|---|
| 2 microsserviços | Isolamento de falha + alinhamento ao enunciado |
| Outbox + RabbitMQ | Publicação confiável sem acoplar a escrita ao consolidado |
| DB por serviço | Fronteira clara de domínio |
| Streamlit | Front Python rápido para o comerciante |
| Prometheus + Grafana | Observabilidade no Compose (diferencial) |

ADRs: [`docs/arquitetura/adr/`](docs/arquitetura/adr/)

## Roadmap

Ver [`docs/ROADMAP.md`](docs/ROADMAP.md). Entrega final = Etapa 8 concluída.
