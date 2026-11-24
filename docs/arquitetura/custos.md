# Estimativa de custos (infraestrutura e licenças)

Estimativa **orientativa** para demonstrar critério de arquiteto. Valores em USD, ordem de grandeza, região genérica cloud (ex.: AWS/GCP/Azure). Licenças open source = US$ 0.

## Premissas

- Carga baixa/moderada de um comerciante (MVP) e folga para ~50 rps no consolidado.
- Stack 100% open source (Python, FastAPI, Streamlit, PostgreSQL, RabbitMQ, Docker).
- Sem custo de software proprietário no núcleo.

## Cenário A — Local / laboratório (desafio)

| Item | Custo |
|---|---|
| Licenças (OSS) | US$ 0 |
| Cloud | US$ 0 |
| Máquina do desenvolvedor | já existente |
| **Total mensal** | **US$ 0** |

## Cenário B — Produção pequena (single region)

| Recurso | Spec sugerida | Estimativa mensal |
|---|---|---|
| 2× API (lancamentos + consolidado) | 0.5–1 vCPU, 1 GB | US$ 20–40 |
| Frontend | 0.25–0.5 vCPU | US$ 8–15 |
| PostgreSQL ×2 (managed) | db.t4g.micro/small | US$ 30–60 |
| RabbitMQ (managed ou container) | small | US$ 15–40 |
| Load balancer / TLS | 1 | US$ 15–20 |
| Observabilidade básica | logs + métricas free tier / light | US$ 0–25 |
| Tráfego / storage | baixo | US$ 5–15 |
| **Total estimado** |  | **~US$ 90–215 / mês** |

## Cenário C — Produção com HA

| Adição vs. B | Impacto |
|---|---|
| Multi-AZ / réplicas DB | +60–100% |
| Cluster RabbitMQ (3 nós) | +US$ 40–100 |
| Autoscale APIs | variável com carga |
| **Faixa** | **~US$ 250–500 / mês** |

## Licenças

| Software | Licença | Custo |
|---|---|---|
| Python / FastAPI / Streamlit / SQLAlchemy | OSI-friendly | 0 |
| PostgreSQL | PostgreSQL License | 0 |
| RabbitMQ | MPL 2.0 | 0 |
| Docker Engine (uso desktop/dev) | conforme política Docker Inc. | 0 no lab; validar org |

## Otimizações de custo

1. Começar com Cenário B single-node broker.
2. Um único cluster Postgres lógico com **dois databases** (ainda database-per-service lógico) se o provedor cobrar por instância — mantendo usuários/schemas isolados.
3. Serverless containers (Cloud Run / Azure Container Apps) para APIs se a carga for intermitente.
4. Reservar HA (Cenário C) só quando SLO exigir.

## Conclusão

Para o desafio, o **Cenário A** é suficiente. A arquitetura escolhida **não amarra** a licenças caras e escala para B/C sem redesign do domínio.
