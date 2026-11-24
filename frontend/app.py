from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st

import clients

st.set_page_config(
    page_title="FluxoCaixa",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("FluxoCaixa")
st.caption("Controle de lançamentos e saldo diário consolidado")


def _sidebar_status() -> None:
    st.sidebar.header("Status dos serviços")
    ok_l, detail_l = clients.health(clients.LANCAMENTOS_URL)
    ok_c, detail_c = clients.health(clients.CONSOLIDADO_URL)

    st.sidebar.markdown("**Lançamentos**")
    if ok_l:
        st.sidebar.success("UP")
    else:
        st.sidebar.error("DOWN")
        st.sidebar.caption(detail_l)

    st.sidebar.markdown("**Consolidado**")
    if ok_c:
        st.sidebar.success("UP")
    else:
        st.sidebar.warning("DOWN — lançamentos continuam disponíveis")
        st.sidebar.caption(detail_c)

    st.sidebar.divider()
    st.sidebar.markdown(
        f"""
APIs:
- `{clients.LANCAMENTOS_URL}`
- `{clients.CONSOLIDADO_URL}`

Observabilidade:
- Grafana `http://localhost:3000`
- Prometheus `http://localhost:9090`
"""
    )


def pagina_novo_lancamento() -> None:
    st.subheader("Novo lançamento")
    st.write("Registra crédito ou débito. A consolidação do saldo ocorre de forma assíncrona.")

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo", options=["CREDITO", "DEBITO"])
            valor_str = st.text_input("Valor", value="0.00")
        with col2:
            data_lanc = st.date_input("Data", value=date.today())
            descricao = st.text_input("Descrição", max_chars=255)

        enviado = st.form_submit_button("Registrar", type="primary")

    if not enviado:
        return

    try:
        valor = Decimal(valor_str.replace(",", "."))
    except InvalidOperation:
        st.error("Valor inválido.")
        return

    if valor <= 0:
        st.error("Valor deve ser maior que zero.")
        return

    try:
        criado = clients.criar_lancamento(
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            data_lancamento=data_lanc,
        )
    except clients.ServiceUnavailable as exc:
        st.error(f"Não foi possível registrar: serviço de lançamentos indisponível. ({exc})")
        return
    except clients.ApiError as exc:
        st.error(f"Falha na validação/API: {exc}")
        return

    st.success(
        f"Lançamento {criado.get('id')} registrado "
        f"({criado.get('tipo')} {criado.get('valor')})."
    )
    st.info(
        "O saldo consolidado pode levar alguns segundos para refletir este lançamento "
        "(consistência eventual)."
    )


def pagina_listagem() -> None:
    st.subheader("Lançamentos")
    col1, col2 = st.columns([2, 1])
    with col1:
        filtrar = st.checkbox("Filtrar por data", value=False)
        data_filtro = st.date_input(
            "Data do filtro",
            value=date.today(),
            disabled=not filtrar,
            key="filtro_data",
        )
    with col2:
        st.write("")
        st.write("")
        atualizar = st.button("Atualizar lista")

    if not atualizar and "lancamentos_cache" not in st.session_state:
        atualizar = True

    if atualizar:
        try:
            resultado = clients.listar_lancamentos(
                data_filtro=data_filtro if filtrar else None
            )
            st.session_state["lancamentos_cache"] = resultado
        except clients.ServiceUnavailable as exc:
            st.error(f"Lista indisponível: {exc}")
            return
        except clients.ApiError as exc:
            st.error(str(exc))
            return

    resultado = st.session_state.get("lancamentos_cache") or {"items": [], "total": 0}
    items = resultado.get("items", [])
    st.write(f"Total: **{resultado.get('total', len(items))}**")

    if not items:
        st.info("Nenhum lançamento encontrado.")
        return

    st.dataframe(
        [
            {
                "data": i.get("data_lancamento"),
                "tipo": i.get("tipo"),
                "valor": i.get("valor"),
                "descricao": i.get("descricao"),
                "id": i.get("id"),
                "criado_em": i.get("criado_em"),
            }
            for i in items
        ],
        use_container_width=True,
        hide_index=True,
    )


def pagina_saldo() -> None:
    st.subheader("Saldo diário consolidado")
    st.write(
        "Consulta a projeção do domínio Consolidado. "
        "Se este serviço estiver fora, você ainda pode registrar lançamentos."
    )

    data_ref = st.date_input("Data de referência", value=date.today(), key="saldo_data")
    consultar = st.button("Consultar saldo", type="primary")

    if not consultar:
        return

    try:
        saldo = clients.consultar_saldo(data_ref)
    except clients.ServiceUnavailable as exc:
        st.warning(
            "Consolidado indisponível no momento. "
            "Os lançamentos continuam sendo aceitos e o saldo será atualizado quando o serviço voltar."
        )
        st.caption(str(exc))
        return
    except clients.ApiError as exc:
        st.error(str(exc))
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Data", str(saldo.get("data")))
    col2.metric("Saldo", str(saldo.get("saldo")))
    col3.metric(
        "Atualizado em",
        saldo.get("atualizado_em") or "— (ainda sem eventos neste dia)",
    )

    if not saldo.get("encontrado", True):
        st.info("Ainda não há consolidação para esta data. Saldo exibido como 0.")


def main() -> None:
    _sidebar_status()
    aba1, aba2, aba3 = st.tabs(["Novo lançamento", "Listagem", "Saldo diário"])
    with aba1:
        pagina_novo_lancamento()
    with aba2:
        pagina_listagem()
    with aba3:
        pagina_saldo()


if __name__ == "__main__":
    main()
else:
    main()
