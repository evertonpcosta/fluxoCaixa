# FluxoCaixa

Controle de fluxo de caixa diário (lançamentos + saldo consolidado).

Desafio de Arquiteto de Soluções — stack **100% Python**, com observabilidade (**Prometheus + Grafana**) no Compose.

## Subir tudo

```bash
docker compose up -d --build
```

| Serviço | URL |
|---|---|
| Frontend (Streamlit) | http://localhost:8501 |
| API Lançamentos | http://localhost:8001/health |
| API Consolidado | http://localhost:8002/health |
| RabbitMQ Management | http://localhost:15672 (`fluxo` / `fluxo`) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (`admin` / `admin`) |

Parar:

```bash
docker compose down
```

## Documentação

- Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)
- Arquitetura: [docs/arquitetura/](docs/arquitetura/)
- Diagramas C4: [docs/diagramas/](docs/diagramas/)
- Observabilidade: [docs/arquitetura/observabilidade.md](docs/arquitetura/observabilidade.md)

## API Lançamentos (Etapa 4)

```bash
# criar
curl -s -X POST http://localhost:8001/lancamentos \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"CREDITO","valor":"100.00","descricao":"venda","data_lancamento":"2026-11-24"}'

# listar
curl -s 'http://localhost:8001/lancamentos?data=2026-11-24'
```

Eventos vão para o outbox e o publisher envia para RabbitMQ (`fluxo.caixa` / `lancamento.criado`) sem bloquear a resposta HTTP.

## Status da implementação

- Etapas 1–3: docs, diagramas, infra Docker + Prometheus/Grafana
- Etapa 4: serviço de lançamentos (API + outbox)
- Etapas 5–6: consolidado e UI completa
