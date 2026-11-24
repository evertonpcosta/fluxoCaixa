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

## Status da implementação

- Etapas 1–2: documentação e diagramas
- Etapa 3: infra Docker + esqueletos com `/health` e `/metrics`
- Etapas 4–6: regras de negócio (lançamentos, consolidado, UI completa)
