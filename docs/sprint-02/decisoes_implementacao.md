# Sprint 2 — Decisões e limites
O núcleo da Sprint 1 foi implementado em FastAPI, SQLAlchemy e scikit-learn; o frontend usa React.
O equipamento GoodWe HCA G2/SEMS+ é referência física, sem credenciais de telemetria: os registros são simulados.
O rateio usa energia validada multiplicada pela tarifa e taxa mensal por usuário que possui consumo faturável. Sessões com falha de comunicação aguardam revisão; interrupções validadas usam energia medida.
A IA recebe as mesmas sessões do rateio, mas não interfere automaticamente na cobrança. Previsão com Random Forest e anomalias com Isolation Forest, com recomendações derivadas desses resultados.
Desvios da proposta: não há login/autorização, sistema financeiro real ou faturas persistidas; a fatura é calculada por consulta. O cadastro de usuários e carregadores é feito por seed de demonstração. Não houve acesso à SEMS+ ou ao carregador. APIs complementares foram deixadas fora do escopo.
O frontend React foi simplificado para arquivo único com UMD por CDN, sem build. É apenas uma prova de conceito local, não adequada à produção.
Testes em SQLite, não em PostgreSQL real neste ambiente. Em uso real, exige revisão de segurança, autenticação e qualificação de dados.
Não houve gravação de dados pessoais reais.
