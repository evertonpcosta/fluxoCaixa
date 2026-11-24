# Roadmap — FluxoCaixa

Desafio de Arquiteto de Soluções: controle de fluxo de caixa (lançamentos + consolidado diário).

**Stack definida:** Python em todos os serviços e no frontend.

---

## Visão da solução

| Capacidade | Componente | Tecnologia |
|---|---|---|
| UI do comerciante | `frontend/` | Streamlit (Python) |
| Controle de lançamentos (crédito/débito) | `services/lancamentos/` | FastAPI + PostgreSQL |
| Consolidado diário / saldo | `services/consolidado/` | FastAPI + PostgreSQL |
| Desacoplamento entre serviços | Message broker | RabbitMQ |
| Orquestração local | Docker Compose | Docker |

**NFR crítico:** o serviço de lançamentos permanece disponível mesmo se o consolidado cair (comunicação assíncrona via fila + outbox).

**Carga alvo (consolidado):** ~50 req/s em pico, perda ≤ 5%.

---

## Como usar este roadmap

Cada etapa termina com um **checkpoint**. Nesse ponto você:

1. Revisa os arquivos gerados
2. Faz `git add` / `commit` / `push` (manual — por você)
3. Avisa para seguir para a próxima etapa

---

## Etapa 0 — Repositório e remote *(feita)*

- [x] Remote `origin` → `git@github.com:evertonpcosta/fluxoCaixa.git`
- [ ] Commit/push inicial quando houver conteúdo da Etapa 1

---

## Etapa 1 — Documentação: diagramas C4 *(feita)*

**Objetivo:** apenas diagramas importáveis no [diagrams.net](https://app.diagrams.net/).

| Arquivo | Conteúdo |
|---|---|
| `docs/diagramas/c4-01-context.drawio` | C4 Nível 1 — System Context |
| `docs/diagramas/c4-02-container.drawio` | C4 Nível 2 — Containers |
| `docs/diagramas/c4-03-component-lancamentos.drawio` | C4 Nível 3 — Serviço Lançamentos |
| `docs/diagramas/c4-04-component-consolidado.drawio` | C4 Nível 3 — Serviço Consolidado |
| `docs/diagramas/fluxo-lancamento.drawio` | Fluxo: criar lançamento → evento → consolidação |
| `docs/diagramas/fluxo-consulta-saldo.drawio` | Fluxo: consulta de saldo diário |
| `docs/diagramas/fluxo-isolamento.drawio` | Fluxo: consolidado indisponível (NFR) |

**Como importar:** abra https://app.diagrams.net/ → *File → Open from → Device* → selecione o `.drawio`.

### Checkpoint Etapa 1

```bash
git add docs/ROADMAP.md docs/diagramas/
git commit -m "docs: adiciona roadmap e diagramas C4 do FluxoCaixa"
git push -u origin main
```

⏸ **Pausa** — commit e push por você. Avise para seguir.

---

## Etapa 2 — Documentação textual da arquitetura *(feita)*

- [x] Domínios funcionais e capacidades de negócio → `docs/arquitetura/dominios-e-capacidades.md`
- [x] Requisitos funcionais e não funcionais refinados → `docs/arquitetura/requisitos.md`
- [x] Arquitetura alvo + justificativa de tecnologias → `docs/arquitetura/arquitetura-alvo.md`
- [x] ADRs → `docs/arquitetura/adr/`
- [x] Critérios de segurança de consumo das APIs → `docs/arquitetura/seguranca.md`
- [x] Observabilidade e estimativa de custos → `docs/arquitetura/observabilidade.md`, `custos.md`
- [x] Evoluções futuras → `docs/arquitetura/evolucoes-futuras.md`
- Índice: `docs/arquitetura/README.md`

### Checkpoint Etapa 2

```bash
git add docs/
git commit -m "docs: arquitetura alvo, requisitos e ADRs"
git push
```

⏸ **Pausa** — commit e push por você. Avise para seguir.

---

## Etapa 3 — Infraestrutura base + observabilidade *(feita)*

- [x] `docker-compose.yaml` (Postgres ×2, RabbitMQ, APIs, frontend, **Prometheus**, **Grafana**)
- [x] Dockerfiles: `services/lancamentos`, `services/consolidado`, `frontend`
- [x] `infra/postgres/` (init schemas)
- [x] `infra/prometheus/` + `infra/grafana/` (datasource e dashboard provisionados)
- [x] `infra/rabbitmq/enabled_plugins` (management + prometheus)
- [x] Esqueletos com `/health` e `/metrics`
- [x] `.dockerignore`, `README.md`

### Checkpoint Etapa 3

```bash
git add docker-compose.yaml infra/ .gitignore .dockerignore README.md services/ frontend/ docs/
git commit -m "chore: infra Docker, Prometheus/Grafana e esqueleto dos serviços"
git push
```

Validação local sugerida:

```bash
docker compose up -d --build
# Grafana http://localhost:3000  |  Prometheus http://localhost:9090
```

⏸ **Pausa** — commit e push por você. Avise para seguir.

---

## Etapa 4 — Serviço de Lançamentos (Python / FastAPI) *(feita)*

- [x] Modelo de domínio (crédito/débito)
- [x] API REST (`POST /lancamentos`, `GET /lancamentos`)
- [x] Persistência PostgreSQL + padrão Outbox
- [x] Publisher para RabbitMQ (relay em background)
- [x] Testes unitários (`tests/test_domain.py`, `tests/test_schemas.py`)
- [x] Schema SQL em `infra/postgres/lancamentos-init.sql`

### Checkpoint Etapa 4

```bash
git add services/lancamentos/ infra/postgres/lancamentos-init.sql docs/ROADMAP.md
git commit -m "feat: serviço de lançamentos FastAPI com outbox"
git push
```

Testes locais:

```bash
cd services/lancamentos && pip install -r requirements.txt && pytest -q
```

⏸ **Pausa** — commit e push por você. Avise para seguir.

---

## Etapa 5 — Serviço de Consolidado (Python / FastAPI) *(feita)*

- [x] Consumer RabbitMQ (idempotente via `eventos_processados`)
- [x] Agregação de saldo diário (crédito +, débito −)
- [x] API REST (`GET /saldo?data=YYYY-MM-DD`) — dia sem dados retorna saldo `0`
- [x] Isolamento: consumer independente; lançamentos não dependem deste serviço
- [x] Testes unitários (`tests/test_domain.py`)
- [x] Schema SQL em `infra/postgres/consolidado-init.sql`

### Checkpoint Etapa 5

```bash
git add services/consolidado/ infra/postgres/consolidado-init.sql docs/ROADMAP.md README.md
git commit -m "feat: serviço de consolidado diário com consumer assíncrono"
git push
```

Testes locais:

```bash
cd services/consolidado && pip install -r requirements.txt && PYTHONPATH=. pytest -q
```

⏸ **Pausa** — commit e push por você. Avise para seguir.

---

## Etapa 6 — Frontend Python (Streamlit) *(feita)*

- [x] Tela de novo lançamento (débito/crédito)
- [x] Listagem de lançamentos (com filtro por data)
- [x] Consulta de saldo consolidado por data
- [x] Comunicação HTTP (`frontend/clients.py`) com as duas APIs
- [x] UI resiliente: consolidado DOWN não bloqueia lançamentos; aviso amigável no saldo
- [x] Sidebar com health das APIs

### Checkpoint Etapa 6

```bash
git add frontend/ docs/ROADMAP.md README.md
git commit -m "feat: frontend Streamlit para lançamentos e saldo"
git push
```

Abrir: http://localhost:8501

⏸ **Pausa** — commit e push por você. Avise para seguir.

---

## Etapa 7 — Testes de integração, carga e evidências NFR *(feita)*

- [x] `scripts/isolamento_consolidado.py` (RNF-01)
- [x] `scripts/carga_consolidado.py` (~50 rps, perda ≤ 5%)
- [x] `scripts/atraso_saldo.py` (lag evento → saldo)
- [x] `scripts/recuperacao_outbox.py` (RNF-02)
- [x] `scripts/run_all.sh` + `scripts/README.md`
- [x] Templates/evidências em `docs/resultados/`

### Gerar evidências reais (com Docker ligado)

```bash
docker compose up -d --build
pip install -r scripts/requirements.txt
bash scripts/run_all.sh
```

### Checkpoint Etapa 7

```bash
git add scripts/ docs/resultados/ docs/ROADMAP.md README.md
git commit -m "test: evidências de isolamento, carga e NFRs"
git push
```

⏸ **Pausa** — rode os scripts se puder, depois commit/push. Avise para seguir.

---

## Etapa 8 — README final, observabilidade e polish *(atual)*

- [x] README completo (como funciona + como rodar)
- [x] Healthchecks (`/health`), métricas (`/metrics`), logs JSON
- [x] Diferenciais revisados (segurança, custos, obs, evolução)
- [x] Checklist dos requisitos do PDF → `docs/arquitetura/checklist-entrega.md`

### Checkpoint Etapa 8

```bash
git add README.md docs/ services/lancamentos/app/logging_config.py services/lancamentos/app/main.py services/consolidado/app/logging_config.py services/consolidado/app/main.py
git commit -m "docs: README final e polish de observabilidade"
git push
```

✅ **Entrega pronta** no repositório público após este push.

---

## Estrutura alvo do repositório

```text
fluxoCaixa/
├── README.md
├── docker-compose.yaml
├── docs/
│   ├── ROADMAP.md
│   ├── arquitetura/
│   ├── diagramas/
│   └── resultados/
├── frontend/                 # Streamlit + Dockerfile
├── services/
│   ├── lancamentos/          # FastAPI + Dockerfile
│   └── consolidado/          # FastAPI + Dockerfile
├── infra/
│   ├── postgres/
│   ├── rabbitmq/
│   ├── prometheus/
│   └── grafana/
└── scripts/
```

---

## Status

| Etapa | Status |
|---|---|
| 0 Remote | Feito |
| 1 Diagramas C4 | Feito |
| 2 Docs arquitetura | Feito |
| 3 Infra + Grafana/Prometheus | Feito |
| 4 Lançamentos | Feito |
| 5 Consolidado | Feito |
| 6 Frontend | Feito |
| 7 Testes/NFR | Feito |
| 8 Polish | Em andamento (aguardando commit/push) |
