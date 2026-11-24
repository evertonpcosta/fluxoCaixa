# Critérios de segurança para consumo das APIs

Documento diferencial do desafio: define **como** as APIs devem ser consumidas com segurança (MVP local + diretrizes de produção).

## Superfície de ataque

| Superfície | Exposição MVP | Risco |
|---|---|---|
| API Lançamentos (`:8001`) | Rede Docker / localhost | Injeção de payload, abuso de escrita |
| API Consolidado (`:8002`) | Rede Docker / localhost | Abuso de leitura sob carga |
| Frontend (`:8501`) | Browser local | Input malicioso repassado às APIs |
| RabbitMQ (`:5672` / `:15672`) | Interno (+ UI management) | Acesso indevido à fila |
| PostgreSQL | Somente rede interna | Vazamento se porta publicada |

## Critérios de consumo (contrato de integração)

### 1. Transporte

| Ambiente | Critério |
|---|---|
| Local (Compose) | HTTP na rede interna Docker |
| Produção | **HTTPS/TLS** obrigatório (terminação no gateway ou sidecar) |

### 2. Autenticação / autorização (diretriz)

No MVP do desafio a auth pode estar desabilitada para facilitar demo. Em produção:

| Critério | Detalhe |
|---|---|
| Autenticação | Bearer JWT (ou mTLS serviço-a-serviço) |
| Autorização | Escopos: `lancamentos:write`, `lancamentos:read`, `saldo:read` |
| Front → API | Token de usuário |
| Serviço → Broker | Credenciais dedicadas (não reutilizar user do app) |

### 3. Validação de entrada

- Schemas Pydantic estritos (tipo enum `CREDITO`/`DEBITO`, `valor > 0`, data ISO).
- Rejeitar campos desconhecidos quando fizer sentido (`extra = forbid`).
- Limitar tamanho de `descricao` (ex.: 255 chars).

### 4. Proteção contra abuso

| Controle | Lançamentos | Consolidado |
|---|---|---|
| Rate limit (produção) | Por IP/token na escrita | Por IP/token na leitura (~50 rps alvo) |
| Timeouts no cliente | Sim | Sim (UI não trava) |
| Body size limit | Sim (proxy/uvicorn) | Sim |

### 5. Dados sensíveis

- Não logar payload completo com dados pessoais desnecessários.
- Credenciais apenas em variáveis de ambiente / secrets.
- Não versionar `.env` com senhas reais.

### 6. Mensageria

- Fila/exchange com usuário de aplicação de privilégio mínimo.
- Management UI (15672) **não** exposta publicamente em produção.
- Mensagens sem dados secretos além do necessário ao saldo (id, tipo, valor, data).

### 7. Headers e respostas

| Prática | Aplicação |
|---|---|
| Não vazar stack trace ao cliente | Handler global de erros |
| Correlation-ID | Aceitar/gerar `X-Request-Id` |
| CORS | Restringir origem do front em produção |

## Checklist mínimo antes de exposição pública

- [ ] TLS
- [ ] AuthN/AuthZ
- [ ] Secrets fora do código
- [ ] Rate limit no consolidado
- [ ] RabbitMQ e Postgres sem portas públicas
- [ ] Health público separado de endpoints de negócio (se necessário)
