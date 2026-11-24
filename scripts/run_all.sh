#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> atraso_saldo"
python3 scripts/atraso_saldo.py

echo "==> carga_consolidado"
python3 scripts/carga_consolidado.py --rps 50 --duration 10

echo "==> isolamento_consolidado"
python3 scripts/isolamento_consolidado.py

echo "==> recuperacao_outbox"
python3 scripts/recuperacao_outbox.py

echo "Evidências em docs/resultados/*.json"
