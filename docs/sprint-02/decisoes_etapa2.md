# Etapa 2 — Decisões técnicas de inteligência artificial

**Conformidade com Sprint 1:** Python/FastAPI, PostgreSQL (configuração padrão), scikit-learn, previsão de demanda, detecção de anomalias e recomendações operacionais.

1. **Origem dos dados:** as sessões vêm do mesmo ORM/SQLAlchemy e da mesma sessão de banco usados para rateio e cadastro. Apenas `validado=true` e estados `concluida` ou `interrompida` alimentam a IA. `falha_comunicacao` pendente não treina modelos nem é faturada.
2. **Volume para desenvolvimento:** o seed inicial de três sessões é insuficiente para treino. Foi criado `app.seed_history`, que adiciona 99 registros determinísticos sintéticos de julho a setembro (datas e valores artificiais, sem API real). O seed é opt-in e idempotente.
3. **Previsão:** `RandomForestRegressor`, 7 características por dia, 80 árvores, validação temporal sem shuffle e comparação com baseline da média móvel 7 dias. A avaliação de teste é um-passo-à-frente com observações passadas reais; os sete dias publicados usam previsão recursiva. São avaliações diferentes, não equivalentes.
4. **Aviso de qualidade:** nas condições do seed de demonstração, o RF pode ficar pior que o baseline. Não esconder a métrica: a rota de recomendações desaconselha qualquer automatização quando isso acontece.
5. **Anomalias:** `IsolationForest(contamination=0.08, random_state=42)` sobre duração, energia, potência média, hora, dia da semana e interrupção. A classificação é puramente estatística. Scores não significam culpa nem diagnóstico técnico.
6. **Recomendações:** regras determinísticas usando os resultados calculados dos dois modelos; não são respostas geradas por LLM. A IA está conectada ao fluxo central e à API, mas não controla equipamentos reais.
7. **Proteções:** retornos de `dados_insuficientes` em bases pequenas. Sesões inválidas/pendentes são excluídas; previsões não podem ser negativas; IDs históricos não se repetem. Limite de 365 dias na série diária de previsão; em operação real seria necessário ajustar tamanho de amostra, validação, isolamento multicarregador e monitoramento de drift.
8. **Limites:** demonstração executada em SQLite nos testes. PostgreSQL é previsto por compose/`DATABASE_URL`, mas requer teste na máquina de quem entregará. Ainda não há React, integração GoodWe/SEMS+, login nem acionamento físico.

**Adaptação na Sprint 2:** a Sprint 1 definiu o papel da IA, mas não especificou o conjunto de atributos, mínimos de dados, algoritmo de avaliação ou política de previsão recursiva. Essas escolhas foram detalhadas aqui sem alterar as tecnologias ou objetivos originais.
