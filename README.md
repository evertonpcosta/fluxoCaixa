# Fluxo de Caixa

Dois serviços para o caixa do comerciante.

Lançamentos, na porta 8001, grava crédito e débito. Consolidado, na porta 8002, devolve o saldo do dia.

O lançamento grava no próprio banco, junto com o evento, e um publicador manda o evento para o Redis. O consolidado só lê a fila. Se ele cair, o caixa continua aceitando lançamento. O saldo atrasa até a fila esvaziar. Se a fila for perdida, a outbox republica o período.

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

```bash
curl -s "http://localhost:8002/v1/saldos/11111111-1111-1111-1111-111111111111?data=2026-11-23"
```

```bash
curl -s "http://localhost:8001/v1/lancamentos?comerciante_id=11111111-1111-1111-1111-111111111111"
```

Republicar um período se a fila tiver sido truncada:

```bash
curl -s -X POST http://localhost:8001/v1/outbox/republicar \
  -H 'Content-Type: application/json' \
  -d '{"data_inicio":"2026-11-23","data_fim":"2026-11-23"}'
```

## Testes

```bash
python3 -m unittest discover -s services/lancamentos/tests -t services/lancamentos
python3 -m unittest discover -s services/consolidado/tests -t services/consolidado
```

Validações de carga, atraso do saldo, isolamento e recuperação (stack no ar):

```bash
python3 scripts/carga_consolidado.py --rps 50 --segundos 60
python3 scripts/atraso_saldo.py --amostras 20
python3 scripts/isolamento_consolidado.py
python3 scripts/recuperacao_outbox.py
```

Na carga, só HTTP 2xx conta como sucesso.

## Documentação

- [Arquitetura, aceite, produção e diferenciais](docs/arquitetura.md)
- [Resultado da carga 50 rps](docs/resultados/carga-consolidado.md)
- [Atraso do saldo ≤ 5s](docs/resultados/atraso-saldo.md)
- [Isolamento com consolidado parado](docs/resultados/isolamento-consolidado.md)
- [Recuperação via outbox](docs/resultados/recuperacao-outbox.md)
