# Como usar Prometheus e Grafana

Depois de subir a stack, os targets já são scrapeados — mas o dashboard só fica “vivo” com **tráfego de negócio**. Sem requests nas APIs, quase não há séries `http_requests_*`, `outbox_pending` nem eventos do consumer.

## 1. Subir a stack

```bash
docker compose up -d --build
```

| URL | Uso |
|---|---|
| http://localhost:3000 | Grafana (`admin` / `admin`) |
| http://localhost:9090 | Prometheus |
| http://localhost:8001/metrics | Métricas da API Lançamentos |
| http://localhost:8002/metrics | Métricas da API Consolidado |
| http://localhost:15692/metrics | Métricas do RabbitMQ |

## 2. Gerar dados de observabilidade

```bash
pip install -r scripts/requirements.txt
python3 scripts/gerar_observabilidade.py
```

Padrão: ~90s a 5 ciclos/s (cada ciclo = `POST /lancamentos` + `GET /lancamentos` + `GET /saldo`).

Opções:

```bash
# mais tráfego / mais tempo (melhor para demos)
python3 scripts/gerar_observabilidade.py --duration 180 --rps 10

# carga leve
python3 scripts/gerar_observabilidade.py --duration 60 --rps 3
```

O script grava evidência em `docs/resultados/gerar-observabilidade.json`.

## 3. Ver no Grafana

1. Abra http://localhost:3000 e entre com `admin` / `admin`
2. Menu **Dashboards** → pasta **FluxoCaixa** → **FluxoCaixa — Overview**
3. No canto superior direito, selecione **Last 15 minutes** (ou *Last 5 minutes*)
4. Painéis esperados após o gerador:
   - HTTP requests /s (lançamentos + consolidado)
   - Latência HTTP p95
   - Outbox pendente
   - RabbitMQ messages ready
   - Eventos processados /s
   - Targets UP

Se os gráficos ainda estiverem vazios, espere 15–30s (scrape a cada 10s) e clique em refresh.

## 4. Conferir no Prometheus

http://localhost:9090/graph — exemplos:

```promql
rate(http_requests_total[1m])
histogram_quantile(0.95, sum by (le, service) (rate(http_request_duration_seconds_bucket[1m])))
outbox_pending
consolidado_events_processed_total
up
```

Targets: http://localhost:9090/targets (todos devem estar **UP**).

## 5. Fluxo contínuo (opcional)

Em um terminal separado, deixe o gerador rodando enquanto analisa o dashboard:

```bash
python3 scripts/gerar_observabilidade.py --duration 600 --rps 4
```

## Troubleshooting

| Sintoma | O que checar |
|---|---|
| Targets DOWN | `docker compose ps` e logs dos serviços |
| Dashboard vazio | Rodou `gerar_observabilidade.py`? Range de tempo no Grafana? |
| Só `up` / process metrics | Normal sem tráfego — rode o gerador |
| RabbitMQ sem série de fila | Faça alguns POSTs; a fila `consolidado.lancamento.criado` passa a aparecer |
