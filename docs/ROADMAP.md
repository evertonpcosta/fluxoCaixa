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

- [x] Remote `origin` → `https://github.com/evertonpcosta/fluxoCaixa.git`
- [ ] Commit/push inicial quando houver conteúdo da Etapa 1

---

## Etapa 1 — Documentação: diagramas C4 *(atual)*

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

## Etapa 2 — Documentação textual da arquitetura

- Domínios funcionais e capacidades de negócio
- Requisitos funcionais e não funcionais refinados
- Arquitetura alvo + justificativa de tecnologias
- ADRs (Async messaging, DB por serviço, Streamlit, FastAPI)
- Critérios de segurança de consumo das APIs
- Observabilidade e estimativa de custos (diferenciais)
- Evoluções futuras

### Checkpoint Etapa 2

```bash
git add docs/
git commit -m "docs: arquitetura alvo, requisitos e ADRs"
git push
```

⏸ **Pausa** — commit e push.

---

## Etapa 3 — Infraestrutura base

- `docker-compose.yaml` (Postgres ×2, RabbitMQ, serviços, frontend)
- `infra/postgres/` (init schemas)
- `.gitignore`, `.dockerignore`, `README.md` esqueleto
- Estrutura de pastas dos serviços e do front

### Checkpoint Etapa 3

```bash
git add docker-compose.yaml infra/ .gitignore .dockerignore README.md services/ frontend/
git commit -m "chore: infra Docker e estrutura dos serviços Python"
git push
```

⏸ **Pausa** — commit e push.

---

## Etapa 4 — Serviço de Lançamentos (Python / FastAPI)

- Modelo de domínio (crédito/débito)
- API REST (`POST /lancamentos`, `GET /lancamentos`)
- Persistência PostgreSQL + padrão Outbox
- Publisher para RabbitMQ
- Testes unitários

### Checkpoint Etapa 4

```bash
git add services/lancamentos/
git commit -m "feat: serviço de lançamentos FastAPI com outbox"
git push
```

⏸ **Pausa** — commit e push.

---

## Etapa 5 — Serviço de Consolidado (Python / FastAPI)

- Consumer RabbitMQ (idempotente)
- Agregação de saldo diário
- API REST (`GET /saldo?data=YYYY-MM-DD`)
- Isolamento: queda do consolidado não derruba lançamentos
- Testes unitários

### Checkpoint Etapa 5

```bash
git add services/consolidado/
git commit -m "feat: serviço de consolidado diário com consumer assíncrono"
git push
```

⏸ **Pausa** — commit e push.

---

## Etapa 6 — Frontend Python (Streamlit)

- Tela de novo lançamento (débito/crédito)
- Listagem de lançamentos
- Consulta de saldo consolidado por data
- Comunicação HTTP com os dois serviços
- Tratamento de indisponibilidade do consolidado (UI resiliente)

### Checkpoint Etapa 6

```bash
git add frontend/
git commit -m "feat: frontend Streamlit para lançamentos e saldo"
git push
```

⏸ **Pausa** — commit e push.

---

## Etapa 7 — Testes de integração, carga e evidências NFR

- Scripts de isolamento (consolidado down → lançamentos ok)
- Script de carga (~50 req/s no consolidado)
- Evidências em `docs/resultados/`
- Testes automatizados ponta a ponta (quando couber)

### Checkpoint Etapa 7

```bash
git add scripts/ docs/resultados/ services/*/tests/
git commit -m "test: evidências de isolamento, carga e NFRs"
git push
```

⏸ **Pausa** — commit e push.

---

## Etapa 8 — README final, observabilidade e polish

- README completo (como rodar localmente)
- Healthchecks, logs estruturados, métricas básicas
- Revisão dos diferenciais (segurança, custos, evolução)
- Conferência dos requisitos obrigatórios do PDF

### Checkpoint Etapa 8

```bash
git add README.md docs/ services/ frontend/
git commit -m "docs: README final e polish de observabilidade"
git push
```

✅ **Entrega pronta** no repositório público.

---

## Estrutura alvo do repositório

```text
fluxoCaixa/
├── README.md
├── docker-compose.yaml
├── docs/
│   ├── ROADMAP.md
│   ├── arquitetura/
│   ├── diagramas/          # .drawio (Etapa 1)
│   └── resultados/         # evidências NFR
├── frontend/               # Streamlit (Python)
├── services/
│   ├── lancamentos/        # FastAPI
│   └── consolidado/        # FastAPI
├── infra/postgres/
└── scripts/                # carga / isolamento
```

---

## Status

| Etapa | Status |
|---|---|
| 0 Remote | Feito |
| 1 Diagramas C4 | Em andamento |
| 2 Docs arquitetura | Pendente |
| 3 Infra | Pendente |
| 4 Lançamentos | Pendente |
| 5 Consolidado | Pendente |
| 6 Frontend | Pendente |
| 7 Testes/NFR | Pendente |
| 8 Polish | Pendente |
