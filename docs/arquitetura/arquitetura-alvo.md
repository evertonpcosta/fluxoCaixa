# Arquitetura alvo

## Visão geral

Arquitetura de **microsserviços leves** em Python, com **dois bounded contexts** de backend e um frontend Python, desacoplados por **mensageria**.

```text
Comerciante
    │
    ▼
Frontend (Streamlit / Python)
    │                    │
    │ HTTP               │ HTTP
    ▼                    ▼
API Lançamentos      API Consolidado
(FastAPI)            (FastAPI + consumer)
    │                    ▲
    │ SQL                │ SQL
    ▼                    │
PostgreSQL           PostgreSQL
Lançamentos          Consolidado
(+ outbox)               ▲
    │                    │
    └──► RabbitMQ ───────┘
         (eventos)
```

Diagramas detalhados: [../diagramas/](../diagramas/).

## Estilo arquitetural escolhido

| Opção | Avaliação | Decisão |
|---|---|---|
| Monólito modular | Simples, mas dificulta provar isolamento (RNF-01) | Não |
| Microsserviços (2 serviços) | Alinha ao enunciado e ao NFR de isolamento | **Sim** |
| Serverless puro | Bom para escala, overhead de setup no desafio local | Não (MVP) |
| SOA clássico (ESB) | Overengineering para o problema | Não |

**Conclusão:** dois serviços + broker + front. Escopo pequeno o suficiente para ser operável localmente e grande o suficiente para demonstrar decisões de arquiteto.

## Componentes da arquitetura alvo

| Componente | Papel | Tecnologia |
|---|---|---|
| Frontend | Experiência do comerciante | Python + Streamlit |
| API Lançamentos | Comando/consulta de lançamentos; outbox | Python + FastAPI + SQLAlchemy |
| API Consolidado | Consulta de saldo; consumer de eventos | Python + FastAPI + SQLAlchemy |
| Message broker | Desacopla escrita de consolidação | RabbitMQ |
| DB Lançamentos | Fonte da verdade dos lançamentos | PostgreSQL |
| DB Consolidado | Projeção de saldo diário | PostgreSQL |
| Orquestração local | Subir stack completa | Docker Compose |

## Padrões aplicados

| Padrão | Onde | Por quê |
|---|---|---|
| Database per service | Cada API tem seu Postgres | Autonomia e isolamento de falha |
| Transactional Outbox | Lançamentos | Publicação confiável sem dual-write frágil |
| Domain events | `LancamentoCriado` | Integração assíncrona entre contextos |
| Idempotent consumer | Consolidado | Reprocessamento seguro após falhas |
| API composition no front | Streamlit chama as duas APIs | UI única sem criar BFF no MVP |

## Fluxos principais

1. **Criar lançamento** — ver `fluxo-lancamento.drawio`
2. **Consultar saldo** — ver `fluxo-consulta-saldo.drawio`
3. **Isolamento sob falha** — ver `fluxo-isolamento.drawio`

## Justificativa de tecnologias

### Python (linguagem única)

- Domínio do candidato e requisito do projeto (“linguagem que você domina”).
- Ecossistema maduro para API (FastAPI), mensageria e UI rápida (Streamlit).
- Facilita manutenção e onboarding: um runtime só.

### FastAPI (APIs)

- Tipagem + OpenAPI automático (documentação de contrato).
- Alta performance em I/O assíncrono (adequado a ~50 req/s locais).
- Validação nativa com Pydantic (RNF-09).

### Streamlit (frontend)

- Front 100% Python, alinhado à stack.
- Produtivo para demonstrar RF-11 a RF-14 sem construir SPA.
- Suficiente para o comerciante operar lançamentos e saldo.

### PostgreSQL (dois bancos)

- ACID para outbox transacional.
- Adequado a consultas de saldo por data.
- Dois bancos = fronteira física entre domínios.

### RabbitMQ

- Fila clássica, fácil de operar no Compose.
- Buffer natural quando consolidado está down (RNF-01/02).
- Alternativas (Kafka, Redis Streams) seriam válidas; RabbitMQ tem menor atrito no desafio.

### Docker Compose

- Reprodutibilidade local (RNF-13).
- Espelha a arquitetura alvo sem cloud obrigatória no MVP.

## Arquitetura de transição

Não há legado obrigatório no enunciado. A “transição” neste projeto é do **zero → MVP desacoplado**:

| Fase | Entrega |
|---|---|
| T0 | Diagramas e decisões (Etapas 1–2) |
| T1 | Infra + serviços + front locais |
| T2 | Evidências de NFR (isolamento e carga) |
| Futuro | Auth, observabilidade completa, cloud — ver [evolucoes-futuras.md](evolucoes-futuras.md) |

Se existisse um monolito legado de caixa, a transição recomendada seria: *strangler* extraindo consolidado primeiro (leitura/projeção) e depois a escrita de lançamentos — mantendo eventos como contrato anti-corrupção.

## Trade-offs aceitos no MVP

| Trade-off | Motivo |
|---|---|
| Consistência eventual do saldo | Isolamento e disponibilidade da escrita |
| Streamlit em vez de SPA | Velocidade e stack Python única |
| Sem auth forte no MVP | Foco nos NFRs do enunciado; auth em evolução |
| Um nó de RabbitMQ local | Suficiente para demonstração; cluster em produção |
