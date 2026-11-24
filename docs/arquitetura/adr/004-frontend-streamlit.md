# ADR-004 — Frontend em Python com Streamlit

- **Status:** Aceito
- **Data:** 2026-11-24

## Contexto

O projeto precisa de uma interface para o comerciante comunicar-se com os serviços. A stack backend é Python; manter o front na mesma linguagem reduz atrito.

## Decisão

Usar **Streamlit** como frontend:

- páginas para criar/listar lançamentos e consultar saldo;
- clientes HTTP (`httpx`) para as duas APIs;
- tratamento de timeout/erro quando consolidado estiver indisponível.

## Alternativas consideradas

| Alternativa | Prós | Contras |
|---|---|---|
| React/Vue SPA | UX rica | Segunda linguagem + build |
| FastAPI + Jinja/HTMX | Leve, server-rendered | Mais boilerplate que Streamlit |
| Gradio | Rápido | Menos adequado a fluxo operacional multi-página |

## Consequências

- Demo rápida e alinhada ao desafio.
- Limitações de UX do Streamlit aceitas no MVP.
- Em evolução, pode ser substituído por SPA sem mudar os contratos das APIs.
