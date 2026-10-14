# Decisões técnicas — Sprint 2 | Etapa 1

Este documento registra escolhas que concretizam (ou delimitam provisoriamente) o planejamento da Sprint 1.

| Tema | Decisão da etapa 1 | Racional/impacto |
|---|---|---|
| Banco de dados | SQLAlchemy conectado a PostgreSQL | Mantém a escolha da Sprint 1. Testes automatizados usam SQLite isolado; validar em PostgreSQL na máquina de desenvolvimento. |
| Fonte dos dados | Seed com dados sintéticos determinísticos | Sem credenciais para telemetria real GoodWe/SEMS+. Não afirmar integração física. |
| Fatura | Rateio calculado dinamicamente por mês; ainda **não persistido** como entidade `Fatura` | Evita divergência durante a construção; definir armazenamento e status de pagamento na etapa seguinte, caso seja necessário ao escopo final. |
| Tarifa | R$ 0,90/kWh no exemplo; configurável por `TARIFA_KWH` | Replica exemplo-base; não representa tarifa comercial real. |
| Manutenção | R$ 5,00/mês, cobrada uma vez por usuário com consumo faturável >0 | Periodicidade detalhada agora; não estava especificada na Sprint 1. |
| Sessões incompletas | `falha_comunicacao` não validada é pendência não cobrada | Evita cobrança sem medição verificada. |
| Mês de faturamento | Mês local do **início da sessão**, considerando São Paulo | Regra explícita para sessões que cruzam a meia-noite e fronteiras de mês. |
| Horários | Entrada obrigatoriamente com offset de fuso; armazenamento UTC | Evita ambiguidade nos filtros e intervalos. |
| IA | Não implementada nesta etapa | Próxima etapa usará exatamente as sessões registradas na base para previsão, anomalias e recomendações. |
| Interface | Não implementada nesta etapa | React será ligado à API nas etapas seguintes. |
| Autenticação, pagamento e telemetria | Fora desta etapa inicial | Não simular segurança ou integração física sem implementação correspondente. |

## Transparência e verificações pendentes

- O protótipo completo **ainda não** está pronto para entrega à FIAP; falta IA estrutural, dashboard, evidências reais, README final e histórico de commits.
- Os arquivos originais em `docs/` da Sprint 1 devem ser preservados e inspecionados antes da entrega.
- Corrigir os exemplos de faturas que, na Sprint 1, apareciam como números ilustrativos não derivados da mesma tarifa.
- Antes da nota final, rodar `pytest` no Windows, subir PostgreSQL e verificar pelo menos um registro e uma consulta de faturas na API.
