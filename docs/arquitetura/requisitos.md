# Requisitos funcionais e não funcionais

## Requisitos funcionais (RF)

### Domínio Lançamentos

| ID | Requisito | Prioridade |
|---|---|---|
| RF-01 | Registrar lançamento de crédito com valor, descrição e data | Obrigatório |
| RF-02 | Registrar lançamento de débito com valor, descrição e data | Obrigatório |
| RF-03 | Rejeitar lançamento com valor ≤ 0 ou tipo inválido | Obrigatório |
| RF-04 | Listar lançamentos (com filtro opcional por data) | Obrigatório |
| RF-05 | Após persistir, publicar evento `LancamentoCriado` de forma confiável | Obrigatório |

### Domínio Consolidado

| ID | Requisito | Prioridade |
|---|---|---|
| RF-06 | Consumir `LancamentoCriado` e atualizar saldo do dia | Obrigatório |
| RF-07 | Crédito soma; débito subtrai no saldo da data do lançamento | Obrigatório |
| RF-08 | Consultar saldo diário por data (`GET /saldo?data=YYYY-MM-DD`) | Obrigatório |
| RF-09 | Processamento idempotente (mesmo evento não altera saldo duas vezes) | Obrigatório |
| RF-10 | Dia sem lançamentos retorna saldo 0 (ou 404 — decisão documentada na API) | Obrigatório |

### Experiência do comerciante (Frontend)

| ID | Requisito | Prioridade |
|---|---|---|
| RF-11 | Tela para criar lançamento (débito/crédito) | Obrigatório |
| RF-12 | Tela/listagem de lançamentos | Obrigatório |
| RF-13 | Tela de consulta de saldo por data | Obrigatório |
| RF-14 | Se consolidado estiver indisponível, UI de lançamentos continua operacional | Obrigatório |

---

## Requisitos não funcionais (RNF)

### Disponibilidade e isolamento

| ID | Requisito | Meta |
|---|---|---|
| RNF-01 | Serviço de lançamentos **não** fica indisponível se o consolidado cair | Isolamento total no caminho de escrita |
| RNF-02 | Eventos não consumidos devem ser recuperáveis após retorno do consolidado | Zero perda de lançamentos aceitos |

### Desempenho e carga

| ID | Requisito | Meta |
|---|---|---|
| RNF-03 | Em pico, consolidado recebe ~50 requisições/s | Sustentar carga de consulta |
| RNF-04 | Perda máxima de requisições sob pico | ≤ 5% |
| RNF-05 | Latência típica de consulta de saldo (local) | p95 &lt; 200 ms (alvo local) |

### Consistência

| ID | Requisito | Meta |
|---|---|---|
| RNF-06 | Consistência entre lançamento aceito e saldo | Eventual (segundos) |
| RNF-07 | Persistência de lançamento + outbox | Mesma transação (atômico) |

### Segurança

| ID | Requisito | Meta |
|---|---|---|
| RNF-08 | Comunicação entre front e APIs | HTTP interno; em produção HTTPS |
| RNF-09 | Validação de entrada | Schema estrito (Pydantic) |
| RNF-10 | Critérios de consumo das APIs | Ver [seguranca.md](seguranca.md) |

### Observabilidade

| ID | Requisito | Meta |
|---|---|---|
| RNF-11 | Healthcheck por serviço | `/health` |
| RNF-12 | Logs estruturados do fluxo crítico | correlation/event id |

### Operação

| ID | Requisito | Meta |
|---|---|---|
| RNF-13 | Execução local reproduzível | Docker Compose |
| RNF-14 | Documentação e README | Como rodar e como funciona |
| RNF-15 | Testes automatizados dos domínios | Unitários + evidências NFR |

---

## Fora de escopo (MVP deste desafio)

- Multi-tenant / múltiplos comerciantes
- Conciliação bancária / Open Finance
- Contas a pagar/receber com vencimento
- UI mobile nativa
- Autenticação corporativa (IdP) — prevista em evoluções
