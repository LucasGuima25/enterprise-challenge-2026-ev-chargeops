# Guia de demonstração e pitch — Sprint 2 (5 minutos)

**Enterprise Challenge 2026 — GoodWe + FIAP | Grupo 20.** Este guia é material de estudo e apresentação; o pitch deve ser explicado com compreensão própria do código, não lido mecanicamente.

## Preparação
1. Abra o projeto no computador e execute `INICIAR_DEMO_WINDOWS.bat` (ou `INICIAR_POSTGRES_WINDOWS.bat` se PostgreSQL e Docker já estiverem validados).
2. Deixe abertas: interface `http://127.0.0.1:5173/`, API `http://127.0.0.1:8000/docs`, README e código `backend/app/billing.py`/`backend/app/intelligence.py`.
3. Antes de apresentar, confirme que as abas **Visão geral, Sessões de recarga, Rateio e faturas, Inteligência artificial** carregam. Use apenas dados fictícios.
4. Se não for possível mostrar o sistema ao vivo, use as capturas de `docs/sprint-02/evidencias/`, identificando-as como evidências de uma execução anterior.

## Cronograma orientativo

### 0:00–0:40 | Problema e arquitetura
**Mostre:** primeira tela e, se possível, `docs/arquitetura-ev-chargeops.png`.
**Explique:** um carregador compartilhado precisa associar usuário, sessão, kWh e cobrança. O EV ChargeOps é um protótipo que transforma sessões em rateio transparente e indicadores de inteligência. A referência física é o GoodWe HCA G2, mas a origem dos registros nesta demo é **simulada**. FastAPI liga frontend React ao banco via SQLAlchemy; o PostgreSQL foi planejado, enquanto SQLite é usado na demo simplificada.

### 0:40–1:55 | Cadastro e integridade
**Mostre:** aba **Sessões de recarga**. Use usuário `U001`, carregador `C001`, início/fim de um horário livre em outubro de 2026, 10 kWh e estado concluído; registre.
**Explique:** `POST /api/sessions` valida usuário, carregador, horários, consumo não negativo e conflito de ocupação. A sessão é persistida; falha de comunicação fica pendente, sem cobrança automática.
**Cuidado:** se já cadastrou a sessão de demonstração, escolha outro dia/horário livre para evitar sobreposição.

### 1:55–2:50 | Rateio auditável
**Mostre:** aba **Rateio e faturas**, período `2026-10`, antes/depois do cadastro; se possível, `backend/app/billing.py`.
**Explique:** `total = soma(kWh válidos) × tarifa por kWh + manutenção mensal` apenas uma vez por usuário com consumo faturável. Usamos `Decimal` para arredondar centavos; sessões interrompidas validadas são cobradas pelo consumo registrado; as não validadas ficam pendentes. Exemplo inicial: `18,5 × R$ 0,90 + R$ 5,00 = R$ 21,65`.

### 2:50–4:00 | IA estrutural, não decorativa
**Mostre:** aba **Inteligência artificial** e `backend/app/intelligence.py`.
**Explique:** os modelos leem a **mesma tabela** de sessões usada no faturamento. A Random Forest prevê demanda diária usando histórico, defasagens e dias da semana; o Isolation Forest aponta sessões estatisticamente atípicas. As recomendações usam esses resultados. O modelo preditivo é avaliado cronologicamente e comparado a uma média móvel: se não supera o baseline, não recomendamos automatizar agendamentos. Anomalia não prova fraude.

### 4:00–4:40 | Testes e evidências
**Mostre:** `docs/sprint-02/evidencias/`, `backend/tests/`, a execução `pytest -q` ou `resultados_testes_finais.txt`.
**Explique:** 28 testes aprovados cobrem cálculo, casos especiais, conflito de horário, validação, integração com a API e IA. Foram geradas cinco capturas da aplicação e saídas de IA em JSON. Evidências foram produzidas com SQLite; PostgreSQL não foi homologado neste ambiente.

### 4:40–5:00 | Decisões e limites
**Mostre:** seção Sprint 2 do README.
**Explique:** preservamos a pesquisa e diagramas da Sprint 1; reduzimos escopo em login, telemetria real e faturas armazenadas porque o objetivo era demonstrar o núcleo de negócio com dados fictícios. Para produção seriam necessários acesso autorizado à GoodWe, autenticação, revisão de segurança e validação com dados operacionais.

## Perguntas prováveis da banca
- **Como impede cobrança incorreta?** Somente sessões validadas e concluídas/interrompidas entram em `GET /api/invoices`; o cálculo monetário usa `Decimal`.
- **Qual é a relação entre rateio e IA?** Ambos fazem consultas sobre registros da mesma tabela, mas a IA não altera a fatura.
- **Qual modelo de IA foi usado?** RandomForestRegressor para série temporal agregada e IsolationForest para sessões atípicas.
- **Como testou?** Testes com dados controlados usando SQLite isolado e cliente de teste FastAPI; comandos no README.
- **Por que não integra a GoodWe de verdade?** Sem credenciais autorizadas para telemetria do HCA G2; no MVP, a origem simulada é rotulada claramente.
- **O que falta para implantação real?** Autenticação/autorização, integração física/SEMS+, PostgreSQL validado, dados reais, avaliação do modelo, segurança e conformidade.

> **Importante:** não afirme ter feito integrações ou validações não realizadas. A nota depende da avaliação e da demonstração individual.
