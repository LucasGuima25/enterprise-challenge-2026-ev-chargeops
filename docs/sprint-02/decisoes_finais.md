# EV ChargeOps | Decisões técnicas finais — Sprint 2

**Projeto:** Enterprise Challenge 2026 — GoodWe + FIAP, Grupo 20.

## Matriz de continuidade

| Compromisso da Sprint 1 | Entregue na Sprint 2 | Limites |
|---|---|---|
| Registro de sessões de recarga | FastAPI, endpoints de cadastro e listagem, validação e verificação de sobreposição | Dados sintéticos/manuais; sem telemetria física GoodWe |
| Consumo individual e rateio | SQLAlchemy, filtro pelo mês local, energia medida × tarifa + taxa mensal uma vez | Fatura calculada, não persistida; sem pagamentos |
| PostgreSQL | Modelagem SQLAlchemy e arquivo Docker Compose para PostgreSQL 16 | Testes executados aqui com SQLite isolado; homologação local PostgreSQL pendente |
| IA de previsão | RandomForestRegressor sobre demanda diária; avaliação cronológica contra média móvel | Dados sintéticos; MAE modelo pode ser pior que baseline |
| IA de anomalias | IsolationForest sobre duração, energia, potência média, horário e interrupção | Score indica atipicidade, não fraude comprovada |
| Recomendações | Regras determinísticas ligadas aos modelos, exibidas no React | Apenas suporte à decisão humana, sem acionar carregador |
| Interface React | SPA React no navegador com 4 telas e formulário integrado à API | React UMD 16 vendorizado para operação sem build; substituição por versão atual antes de produção |
| Integração SEMS+/GoodWe | Modelo de referência do carregador e campo de origem `simulado`/`manual` | **Não** implementado acesso a API real ou equipamento |
| Autenticação/controle de acesso | Não implementado no escopo do MVP executável | Sistema local de demonstração; não publicar em rede pública |

## Mudanças justificadas

1. **Sem telemetria GoodWe/SEMS+ ao vivo:** não há credenciais nem acesso ao equipamento L1. A alimentação simulada torna possível validar lógica e IA sem afirmar acesso físico.
2. **SQLite de apoio:** para permitir avaliação mesmo em computador sem Docker, há um inicializador opcional com SQLite. O banco planejado é PostgreSQL e as entidades SQLAlchemy podem operar nele; a validação PostgreSQL precisa ser feita localmente.
3. **React sem etapa de compilação:** para reduzir dependências e facilitar demonstração da sprint, foram incluídas versões locais MIT do React/ReactDOM 16.0.0. **Não é uma escolha adequada a produção:** requer atualização e testes de segurança antes de hospedagem real. Essa opção preserva a tecnologia React planejada.
4. **Faturas sob demanda, não armazenadas:** o banco mantém sessões e usuários, e a API calcula a fatura atualizada. Isso evita cobranças desatualizadas quando uma sessão muda. Não existe ciclo real de pagamentos.
5. **Sem login no MVP:** evita simular controle de acesso inexistente; somente dados fictícios devem ser utilizados.

## Evidências

- `evidencias/resultados_testes_finais.txt`: testes automatizados, incluindo CORS e fluxo de cadastro.
- `evidencias/ia_resultados_demo.json`: respostas reais da API usando TestClient e SQLite isolado.
- `evidencias/01-dashboard.webp` a `05-cadastro-confirmado.webp`: capturas do React executado em Chromium, com as requisições encaminhadas à API FastAPI real por uma ponte do ambiente de testes (não são desenhos ou telas mockadas). O banco dessas capturas é SQLite local. A ponte foi necessária porque o Chromium de testes bloqueia navegação HTTP/arquivo por política do ambiente; **isso não substitui a validação de execução direta no Windows com PostgreSQL**.

## Validações adicionais recomendadas na máquina de entrega

- Executar `INICIAR_POSTGRES_WINDOWS.bat` no Windows com Docker Desktop iniciado.
- Confirmar que `http://127.0.0.1:8000/docs` e `http://127.0.0.1:5173` abrem sem erros.
- Fazer um cadastro no navegador, atualizar a página e confirmar persistência em PostgreSQL.
- Não incluir `demo.sqlite3`, `.venv`, dados pessoais ou credenciais reais no GitHub.
- Preservar os arquivos anteriores da Sprint 1 já existentes no repositório remoto.

- **Ajuste posterior de interface:** a descrição do rateio passou a consultar a configuração real da API (`GET /api/config`) para refletir mudanças em `TARIFA_KWH` e `MANUTENCAO_MENSAL`.
- **Evidências visuais:** imagens originais da demonstração foram convertidas para WebP para reduzir o tamanho da publicação, sem alterar seu conteúdo.
