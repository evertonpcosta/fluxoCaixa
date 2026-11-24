import os

import httpx
import streamlit as st

LANCAMENTOS_URL = os.getenv("LANCAMENTOS_URL", "http://localhost:8001")
CONSOLIDADO_URL = os.getenv("CONSOLIDADO_URL", "http://localhost:8002")

st.set_page_config(page_title="FluxoCaixa", page_icon="💰", layout="centered")
st.title("FluxoCaixa")
st.caption("Frontend Python (Streamlit) — esqueleto da Etapa 3")

st.info(
    "As telas de lançamentos e saldo serão implementadas nas etapas seguintes. "
    "Use esta página para validar conectividade com as APIs."
)


def check(url: str) -> tuple[bool, str]:
    try:
        response = httpx.get(f"{url}/health", timeout=3.0)
        response.raise_for_status()
        return True, response.text
    except Exception as exc:  # noqa: BLE001 — UI de diagnóstico
        return False, str(exc)


col1, col2 = st.columns(2)

with col1:
    st.subheader("API Lançamentos")
    ok, detail = check(LANCAMENTOS_URL)
    st.success("UP") if ok else st.error("DOWN")
    st.code(detail)

with col2:
    st.subheader("API Consolidado")
    ok, detail = check(CONSOLIDADO_URL)
    st.success("UP") if ok else st.error("DOWN")
    st.code(detail)

st.divider()
st.markdown(
    """
**Observabilidade**

- Grafana: http://localhost:3000 (`admin` / `admin`)
- Prometheus: http://localhost:9090
"""
)
