# ADR-002 — Mensageria assíncrona + Transactional Outbox

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

Após criar um lançamento, o consolidado precisa atualizar o saldo. Chamada síncrona HTTP Lançamentos → Consolidado criaria acoplamento e violaria o NFR de isolamento.

Publicar direto na fila *dentro* do request, sem outbox, gera risco de dual-write (commit no banco ok / publish falhou, ou o inverso).

## Decisão

1. Comunicação **assíncrona** via **RabbitMQ**.
2. Padrão **Transactional Outbox** no serviço de lançamentos:
   - mesma transação grava `lancamento` + linha em `outbox`;
   - processo/relay publica para a fila e marca como enviado.
3. Consumer do consolidado **idempotente** (chave `event_id`).

## Alternativas consideradas

| Alternativa | Prós | Contras |
|---|---|---|
| HTTP síncrono entre serviços | Simples | Viola isolamento |
| Publish direto sem outbox | Menos código | Perda/duplicidade sob falha |
| Kafka | Excelente para log de eventos | Overkill operacional no desafio |
| CDC (Debezium) | Outbox “automático” | Infra pesada para MVP |

## Consequências

- Lançamentos respondem 201 sem depender do consolidado.
- Consistência do saldo é **eventual**.
- Precisa de relay de outbox e monitoramento de lag da fila.

## Refinamento operacional

- O publisher **declara** exchange + fila + bind (não depende do consumer ter subido).
- Publicação usa **publisher confirms** (`confirm_delivery` + `mandatory=True`); só marca outbox após ack do broker.
- Evidência de partida com consolidado DOWN: `scripts/partida_consolidado_down.py`.
