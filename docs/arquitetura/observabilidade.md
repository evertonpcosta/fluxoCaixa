# Monitoramento e observabilidade

Diferencial do desafio. No MVP implementamos a base; o alvo completo fica como evolução.

## Pilares

| Pilar | MVP | Alvo |
|---|---|---|
| Logs | stdout estruturado (JSON) | Agregação (Loki/ELK) |
| Métricas | Contadores básicos / health | Prometheus + Grafana |
| Traces | `X-Request-Id` / `event_id` | OpenTelemetry end-to-end |

## O que observar por componente

### API Lançamentos

- Taxa de `POST /lancamentos` (sucesso/4xx/5xx)
- Lag do outbox (quantidade pendente)
- Falhas de publish no RabbitMQ
- Latência p95 do POST

### API Consolidado

- Taxa de `GET /saldo` (meta: ~50 rps, perda ≤ 5%)
- Latência p95/p99 da consulta
- Throughput do consumer (msgs/s)
- Erros de processamento / requeues
- Tamanho da fila (depth)

### RabbitMQ

- Queue depth `lancamentos.criados`
- Consumers ativos
- Unacked messages

### Frontend

- Erros HTTP por API
- Timeouts para consolidado (sinal de degradação sem derrubar lançamentos)

## Healthchecks

| Endpoint | Significado |
|---|---|
| `GET /health` | Processo no ar |
| `GET /health/ready` (evolução) | DB + dependências críticas ok |

Para **lançamentos**, readiness **não** deve depender do consolidado (reforça RNF-01).  
Dependência do broker pode ser “degradada” (aceita escrita + outbox mesmo se publish imediato falhar).

## SLIs / SLOs sugeridos

| SLI | SLO (produção sugerido) |
|---|---|
| Disponibilidade POST lançamentos | 99.9% mensal |
| Sucesso GET saldo sob carga nominal | ≥ 95% (alinha ao “máx. 5% perda”) |
| Lag de consolidação (evento → saldo) | p95 &lt; 5 s |
| Outbox pendente | Alerta se &gt; N por M minutos |

## Alertas mínimos (produção)

1. Fila crescendo sem consumer
2. Taxa de erro 5xx &gt; limiar
3. Outbox sem drenagem
4. Latência p95 saldo acima do alvo
