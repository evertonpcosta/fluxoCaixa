# Evoluções futuras

Itens que demonstram visão além do MVP (tempo limitado do desafio).

## Curto prazo (pós-MVP)

| Item | Valor |
|---|---|
| Autenticação JWT no front e nas APIs | Segurança de consumo |
| Testes de carga automatizados no CI | Evidência contínua do RNF de 50 rps |
| Alertas Grafana / Alertmanager | Operação (dashboard base já no Compose) |
| `GET /health/ready` diferenciado | Orquestração/k8s |

## Médio prazo

| Item | Valor |
|---|---|
| Versionamento de eventos (`LancamentoCriado` v1/v2) | Evolução sem quebra |
| Dead Letter Queue + replay tool | Operação de falhas |
| Cache de saldo (Redis) com invalidação por evento | Folga para &gt;50 rps |
| BFF opcional se o front virar SPA | Agregação e auth |
| Multi-conta / multi-comerciante (tenant_id) | Produto real |

## Longo prazo / produto

| Item | Valor |
|---|---|
| Conciliação com extrato bancário | Fechamento de caixa |
| Categorias e centros de custo | Análise gerencial |
| Relatórios mensais / export CSV | Contabilidade |
| App mobile | Mobilidade do comerciante |
| OpenTelemetry completo | Diagnóstico distribuído |
| Deploy cloud com IaC (Terraform) | Reprodutibilidade prod |

## O que eu gostaria de ter implementado com mais tempo

1. **Auth + rate limit** de ponta a ponta.
2. **Painel de observabilidade** embutido no Compose (Prometheus/Grafana).
3. **Projeção de atraso do saldo** na UI (“atualizado há Xs”), tornando a consistência eventual explícita ao usuário.
4. **Contrato de eventos** com schema registry leve (JSON Schema versionado no repo).

Esses pontos reforçam a mesma arquitetura — não exigem reescrever os bounded contexts.
