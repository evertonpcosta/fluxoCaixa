# Arquitetura

O comerciante lança crédito e débito e consulta o saldo do dia. São duas capacidades, com vida separada: controlar o lançamento e consolidar o dia.

A restrição que define o desenho é o lançamento continuar de pé se o consolidado cair. No pico, o consolidado recebe 50 req/s, com no máximo 5% de perda.

## Domínios

Controle de lançamentos é a fonte da verdade do movimento. Aceita `CREDITO` ou `DEBITO`, valor positivo com duas casas, data e uma descrição. Não calcula saldo.

Consolidado diário lê o fato já gravado e mantém o saldo do comerciante na data. Créditos somam, débitos subtraem. Evento repetido não entra de novo. Esse domínio não corrige o lançamento original.

Comerciante, aqui, é um id informado por quem chama. Sem cadastro, sem usuário, sem estorno. Se um dia precisar ajustar o caixa, o ajuste é outro lançamento.

## Requisitos e critérios de aceite

### Funcionais

| ID | Requisito | Aceite |
| --- | --- | --- |
| RF01 | Registrar crédito ou débito | `POST /v1/lancamentos` responde 201 e persiste o lançamento |
| RF02 | Recusar valor inválido | valor ≤ 0 ou com mais de duas casas → 422 |
| RF03 | Listar lançamentos | `GET /v1/lancamentos` filtra por comerciante e data |
| RF04 | Consultar saldo do dia | `GET /v1/saldos/{id}?data=` devolve créditos, débitos e saldo |
| RF05 | Processar cada lançamento uma vez | republicar o mesmo evento não altera o saldo |

### Não funcionais

| ID | Requisito | Aceite |
| --- | --- | --- |
| RNF01 | Isolamento | Com consolidado parado, lançamentos respondem 201. Ver [isolamento](resultados/isolamento-consolidado.md) |
| RNF02 | 50 req/s no consolidado | Perda ≤ 5% em 60s a 50 rps. Ver [carga](resultados/carga-consolidado.md) |
| RNF03 | Atraso do saldo | Em operação normal, saldo atualizado em até 5s após o commit do lançamento. Medido: [atraso](resultados/atraso-saldo.md) |
| RNF04 | Recuperação | Após perda do stream, `POST /v1/outbox/republicar` reconstrói o saldo sem duplicidade. Ver [recuperação](resultados/recuperacao-outbox.md) |

### Como a perda é medida

Perda = `(requisições sem sucesso HTTP 2xx / volume enviado) * 100`.

Sucesso é **somente 2xx**. Contam como perda: timeout, conexão recusada, 3xx, 4xx e 5xx. O script `scripts/carga_consolidado.py` grava o critério no JSON (`criterio_sucesso`) junto com volume, erros, timeouts, latências e percentual.

### Como verificar a recuperação

1. Apagar o stream `fluxo.lancamentos` (ou imaginar truncamento prolongado).
2. Se o consolidado já tinha processado, limpar `eventos_processados` e `saldos_diarios` do dia sob teste.
3. Chamar `POST /v1/outbox/republicar` com o intervalo de datas.
4. Esperar o publicador reenviar e o consumidor reaplicar.
5. Conferir o saldo esperado e que uma segunda espera não muda o valor.

## Desenho local (implementado)

Dois processos, dois bancos no mesmo Postgres, uma fila Redis.

```text
cliente -> lançamentos:8001 -> Postgres/lancamentos (lançamento + outbox)
lançamentos -> Redis Stream fluxo.lancamentos
Redis -> consolidado:8002 -> Postgres/consolidado (evento + saldo)
```

O `POST` responde no commit do lançamento. A publicação acontece depois. Com o Redis fora, a outbox segura o evento. Se o processo morre no meio, o evento pode sair duas vezes. O consolidado grava o `evento_id` antes de mexer no saldo, na mesma transação.

Não há `MAXLEN` no `XADD`. A fila pode crescer; a fonte de verdade continua sendo a outbox no Postgres. Se a fila for truncada ou perdida, `POST /v1/outbox/republicar` marca o período e o publicador reenvia. O consumidor é idempotente.

Evento inválido vai para `fluxo.lancamentos.dlq`. Falha de banco não confirma a mensagem.

```json
{
  "evento_id": "uuid do lançamento",
  "lancamento_id": "uuid do lançamento",
  "comerciante_id": "uuid",
  "tipo": "CREDITO",
  "valor": "150.00",
  "descricao": "venda",
  "data_lancamento": "2026-11-23"
}
```

Tabelas: `lancamentos`, `outbox`, `eventos_processados`, `saldos_diarios`.

## Topologia de produção (proposta)

```text
                 +-- ALB/HTTPS --+
                 |               |
           lançamentos x2   consolidado x2
                 |               |
           Postgres A       Postgres B
                 |
              Redis
```

| Componente | Papel | Compartilhado? |
| --- | --- | --- |
| ALB + certificado ACM | TLS na borda | sim, entrada única |
| Serviço lançamentos | escrita e republicação | não compartilha processo com consolidado |
| Serviço consolidado | leitura de saldo e consumo | não compartilha processo com lançamentos |
| Postgres A | dados de lançamento e outbox | dedicado |
| Postgres B | eventos e saldos | dedicado |
| Redis | stream e DLQ | compartilhado entre publisher e consumer |

### Pontos únicos de falha

| Ponto | Impacto se cair | Mitigação |
| --- | --- | --- |
| Redis | atraso do saldo; caixa continua | multi-AZ / réplica; outbox no Postgres; republicar |
| Postgres A | caixa fora | Multi-AZ; backup; RPO baixo |
| Postgres B | consulta de saldo fora; caixa continua | Multi-AZ; republicar após restore |
| ALB | tudo fora pela borda | multi-AZ nativo |
| Uma réplica de serviço | capacity reduzida | mínimo 2 tasks |

### Estratégia de recuperação

1. Falha curta do consolidado: consumer group + `XAUTOCLAIM`. Sem ação manual.
2. Redis perdido ou stream truncado: `POST /v1/outbox/republicar` no intervalo afetado. Implementado.
3. Restore do Postgres B: republicar o período e deixar a idempotência descartar o que já voltou no backup.
4. Pico de leitura: escala horizontal do consolidado no mesmo consumer group.

## Escolhas

Dois serviços porque o caixa e o relatório não podem compartilhar o mesmo processo.

Parei nesses dois. Gateway, mesh ou Kubernetes não mudam o resultado em 50 req/s. Em produção eu colocaria as duas tasks atrás do ALB, sem malha. Python/FastAPI, Postgres e Redis Streams. Dinheiro em `Decimal`.

## Segurança

| Capacidade | Implementado | Proposto |
| --- | --- | --- |
| API key no header `X-API-Key` | sim (`API_KEY`) | | 
| Serviços sem chamada HTTP entre si | sim | |
| TLS na borda | não no Compose local | ALB + ACM (HTTPS only) |
| Credencial por cliente de integração | uma chave só | OAuth2 client credentials, um client_id por sistema |
| Autorização por comerciante | não | claim/scope com lista de `comerciante_id`; API rejeita id fora do escopo |
| Segredo fora do compose | `.env` local | Secrets Manager / Parameter Store |

## Observabilidade

| Item | Implementado | Proposto |
| --- | --- | --- |
| `GET /health` | sim | liveness |
| `GET /ready` | sim | readiness (banco) |
| Log stdout | sim | CloudWatch / Loki |
| Métrica de atraso do consolidado | não instrumentada | `outbox_pendente` (linhas com `publicado_em` nulo) e idade do mais antigo |
| Taxa de erro HTTP | não | `5xx / total` por serviço no ALB/app |
| Alerta atraso | não | outbox pendente > 0 por mais de 60s |
| Alerta erro | não | taxa 5xx > 1% em 5 min |
| Alerta fila | não | lag do consumer group > 1 000 msgs |

## Custo de referência (proposta)

Provedor: AWS. Região: `sa-east-1` (São Paulo). Ambiente único, pico 50 rps, sem reserva. Licença de software: zero.

| Componente | Dimensionamento | Estimativa/mês |
| --- | --- | --- |
| ECS Fargate ou 1× EC2 t3.small | 2 tasks lançamentos + 2 tasks consolidado (ou uma VM) | USD 20–40 |
| RDS Postgres `db.t4g.micro` Multi-AZ (A) | lançamentos/outbox | USD 30–45 |
| RDS Postgres `db.t4g.micro` Multi-AZ (B) | consolidado | USD 30–45 |
| ElastiCache Redis `cache.t4g.micro` | stream | USD 15–25 |
| ALB | TLS e balanceamento | USD 20–25 |
| Tráfego + logs | baixo volume | USD 5–10 |

Total típico: cerca de USD 120–190/mês com bancos separados. Se no início os dois databases ficarem no mesmo RDS, cai para cerca de USD 90–140/mês. Licenças: USD 0.

## Transição

Não há legado neste problema. O primeiro deploy já é o desenho alvo.

Se o caixa hoje fosse planilha: gravar na API, conferir saldo contra a planilha por alguns fechamentos, desligar a planilha.

## Evidências

- [Carga 50 rps](resultados/carga-consolidado.md)
- [Atraso do saldo ≤ 5s](resultados/atraso-saldo.md)
- [Isolamento com consolidado parado](resultados/isolamento-consolidado.md)
- [Recuperação via outbox](resultados/recuperacao-outbox.md)
