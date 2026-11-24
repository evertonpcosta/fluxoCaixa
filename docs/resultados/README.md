# Evidências de NFR

Arquivos gerados pelos scripts em `scripts/`.

| Evidência | JSON | Critério |
|---|---|---|
| Isolamento | [isolamento-consolidado.json](isolamento-consolidado.json) | Lançamentos disponíveis com consolidado DOWN |
| Carga | [carga-consolidado.json](carga-consolidado.json) | ~50 req/s, perda ≤ 5% **e** vazão ≥ 90% do alvo |
| Atraso do saldo | [atraso-saldo.json](atraso-saldo.json) | Consistência eventual (alvo &lt; 5s) |
| Recuperação | [recuperacao-outbox.json](recuperacao-outbox.json) | Drain da fila/outbox após recover |
| Partida consolidado DOWN | [partida-consolidado-down.json](partida-consolidado-down.json) | Fila provisionada pelo publisher + confirm + drain |

Para (re)gerar:

```bash
docker compose up -d --build
pip install -r scripts/requirements.txt
python3 scripts/atraso_saldo.py
python3 scripts/carga_consolidado.py --rps 50 --duration 10
python3 scripts/isolamento_consolidado.py
python3 scripts/recuperacao_outbox.py
```

Os resumos narrativos estão nos `.md` ao lado de cada JSON.
