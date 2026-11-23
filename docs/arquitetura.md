# Arquitetura

O comerciante lança crédito e débito e consulta o saldo do dia. São duas capacidades, com vida separada: controlar o lançamento e consolidar o dia.

A restrição que define o desenho é o lançamento continuar de pé se o consolidado cair. No pico, o consolidado recebe 50 req/s, com perda máxima de 5%.

## Domínios

Controle de lançamentos é a fonte da verdade do movimento. Aceita `CREDITO` ou `DEBITO`, valor positivo com duas casas, data e uma descrição. Não calcula saldo.

Consolidado diário lê o fato já gravado e mantém o saldo do comerciante na data. Créditos somam, débitos subtraem. Evento repetido não entra de novo. Esse domínio não corrige o lançamento original.

Comerciante, aqui, é um id informado por quem chama. Sem cadastro, sem usuário, sem estorno. Se um dia precisar ajustar o caixa, o ajuste é outro lançamento.

## Desenho

Dois processos, dois bancos, uma fila.

```text
cliente -> lançamentos -> Postgres (lançamento + outbox, mesma transação)
lançamentos -> Redis Stream fluxo.lancamentos
Redis -> consolidado -> Postgres (evento processado + saldo do dia)
```

O `POST` responde no commit do lançamento. A publicação acontece depois. Com o Redis fora, a outbox segura o evento e o publicador tenta de novo. Se o processo morre no meio, o evento pode sair duas vezes. O consolidado grava o `evento_id` antes de mexer no saldo, na mesma transação, então a segunda entrega não altera o valor.

Evento inválido vai para `fluxo.lancamentos.dlq` e sai da fila principal. Falha de banco não confirma a mensagem. O consumidor recupera o que ficou pendente.

O evento vai no campo `data` do stream:

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

`evento_id` é o id do lançamento.

Tabelas de lançamentos: `lancamentos` e `outbox` (`publicado_em` nulo até o Redis aceitar). Tabelas do consolidado: `eventos_processados` (chave no `evento_id`) e `saldos_diarios` (chave em comerciante + data).

O esquema é criado na subida. Chega para rodar local. Com dado já em produção, eu trocaria por migração versionada.

## Escolhas

Dois serviços porque o caixa e o relatório não podem compartilhar o mesmo processo. Um defeito no consolidado derrubaria o lançamento.

Parei nesses dois. Gateway, mesh ou Kubernetes não mudam o resultado em 50 req/s e aumentam o que alguém precisa operar. Uma VM com Compose isola os processos. Se a leitura crescer, sobe outra réplica do consolidado no mesmo consumer group. O estado está no Postgres.

Python e FastAPI pela API pequena e pelo contrato em `/docs`. Postgres pela transação da outbox e pelo `NUMERIC`. Redis Streams porque esse pico cabe numa fila com grupo de consumidores. Dinheiro em `Decimal`.

## Carga

50 req/s no consolidado é uma leitura pela chave primária e, na entrada, evento na fila. Uma instância aguenta. Não medi. A conta vem do acesso, não de um teste de carga.

Os 5% são teto. Não descarto requisição de propósito. O que falha de fato é a consulta enquanto o processo reinicia. O lançamento já commitado fica na outbox. Quem consulta tenta de novo.

O `POST` de lançamento fica fora desse orçamento. A fila pode atrasar o relatório sem atrasar o caixa.

## Transição

Não há legado neste problema. O primeiro deploy já é o desenho alvo, os dois processos no mesmo Compose.

Se o caixa hoje fosse planilha, eu gravaria na API e conferiria o saldo contra a planilha por alguns fechamentos antes de desligar a planilha.

## Segurança

Quem integra manda `X-API-Key`. O valor vem de `API_KEY`. Vazio no exemplo local, para o curl do README. Preenchido, as rotas de negócio recusam a chamada.

Os serviços não se chamam por HTTP. A chave é do cliente de fora. Com mais de um sistema consumidor, o caminho é client credentials, um cliente por sistema, TLS na frente. Uma chave só não distingue quem chamou.

O log leva o id do lançamento. A descrição, que pode ter dado da venda, fica de fora.

## Operação e custo

`/health` responde se o processo subiu, sem olhar banco nem fila. `/ready` olha o banco daquele serviço. Log vai para stdout.

Para esse porte, uma VM com os dois containers, um Postgres pequeno e um Redis pequeno. Na casa de 60 a 120 dólares por mês no perfil menor de nuvem, sem reserva. Licença zero.

Os dois bancos podem ficar no mesmo Postgres enquanto o volume for esse. Eu separaria a instância no dia em que o relatório disputasse disco com o caixa. Balanceador só com mais de uma réplica HTTP.

O alerta que eu colocaria primeiro é a outbox acumulando `publicado_em` nulo. Isso mostra relatório atrasado sem tratar o caixa como fora do ar.
