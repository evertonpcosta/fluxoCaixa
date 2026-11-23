# Fluxo de Caixa

Dois serviços para o caixa do comerciante.

Lançamentos, na porta 8001, grava crédito e débito. Consolidado, na porta 8002, devolve o saldo do dia.

O lançamento grava no próprio banco, junto com o evento, e um publicador manda o evento para o Redis. O consolidado só lê a fila. Se ele cair, o caixa continua aceitando lançamento. O saldo atrasa até a fila esvaziar.

## Subir

Docker Compose v2.

```bash
docker compose up --build
```

No exemplo local o Postgres usa usuário e senha `fluxo`. Sem `API_KEY`, as rotas ficam abertas. Para exigir chave:

```bash
API_KEY=uma-senha docker compose up --build
```

O header é `X-API-Key`. OpenAPI em `/docs` de cada porta.

## Uso

```bash
curl -s -X POST http://localhost:8001/v1/lancamentos \
  -H 'Content-Type: application/json' \
  -d '{
    "comerciante_id": "11111111-1111-1111-1111-111111111111",
    "tipo": "CREDITO",
    "valor": "150.00",
    "descricao": "venda",
    "data_lancamento": "2026-11-23"
  }'
```

`tipo` é `CREDITO` ou `DEBITO`. Valor positivo, no máximo duas casas.

```bash
curl -s "http://localhost:8002/v1/saldos/11111111-1111-1111-1111-111111111111?data=2026-11-23"
```

Saldo é créditos menos débitos daquele comerciante na data. Se o evento ainda não foi consumido, a resposta vem zerada e `atualizado_em` nulo.

```bash
curl -s "http://localhost:8001/v1/lancamentos?comerciante_id=11111111-1111-1111-1111-111111111111"
```

## Testes

```bash
python3 -m unittest discover -s services/lancamentos/tests -t services/lancamentos
python3 -m unittest discover -s services/consolidado/tests -t services/consolidado
```

O desenho está em [docs/arquitetura.md](docs/arquitetura.md).
