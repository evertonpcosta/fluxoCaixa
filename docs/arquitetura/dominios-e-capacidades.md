# Domínios funcionais e capacidades de negócio

## Contexto de negócio

Um comerciante precisa controlar o **fluxo de caixa diário**: registrar lançamentos (débitos e créditos) e consultar o **saldo diário consolidado**.

## Mapa de capacidades

```text
Fluxo de Caixa (produto)
├── Capacidade: Registrar movimentação financeira
│   ├── Registrar crédito
│   ├── Registrar débito
│   └── Consultar histórico de lançamentos
│
└── Capacidade: Consolidar posição diária
    ├── Atualizar saldo do dia a partir de eventos
    └── Consultar saldo consolidado por data
```

## Domínios (bounded contexts)

| Domínio | Responsabilidade | Fora do escopo |
|---|---|---|
| **Lançamentos** | Aceitar, validar e persistir movimentações de caixa; publicar fatos de negócio | Calcular saldo |
| **Consolidado** | Consumir fatos, agregar saldo por dia, expor consulta de posição | Criar/alterar lançamentos |
| **Experiência do comerciante** | Interface para operar as duas capacidades | Regras de domínio |

### Por que dois domínios de backend?

1. **Requisito explícito** do desafio: dois serviços (controle de lançamentos + consolidado diário).
2. **NFR de isolamento**: queda do consolidado não pode indisponibilizar lançamentos → fronteiras claras e comunicação assíncrona.
3. **Evolução independente**: o consolidado pode escalar para atender ~50 req/s sem acoplar o caminho crítico de escrita de lançamentos.

## Linguagem ubíqua (glossário)

| Termo | Significado |
|---|---|
| Lançamento | Movimentação financeira de caixa (crédito ou débito) |
| Crédito | Entrada de valor (+) |
| Débito | Saída de valor (−) |
| Saldo diário | Posição consolidada do caixa em uma data |
| Evento `LancamentoCriado` | Fato imutável de que um lançamento foi aceito |
| Consistência eventual | Saldo pode atrasar alguns segundos após o lançamento |

## Cadeia de valor

```text
Comerciante registra lançamento
        → sistema aceita e confirma
        → fato é propagado
        → saldo do dia é atualizado
        → comerciante consulta posição do dia
```

Valor entregue: **controle operacional do caixa** com visão diária confiável, sem bloquear a operação de registro quando a consolidação estiver degradada.
