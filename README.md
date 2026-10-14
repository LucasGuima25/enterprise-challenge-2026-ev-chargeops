# EV ChargeOps — Enterprise Challenge 2026 | GoodWe + FIAP

**Grupo 20 · Sprint 01 (pesquisa/arquitetura) + Sprint 02 (protótipo funcional)**

> **Protótipo acadêmico demonstrativo, sem conexão física com o carregador GoodWe e sem pagamento real.** Todas as sessões fornecidas são fictícias. Não inserir dados pessoais reais.

## 1. Problema e solução

Em infraestrutura compartilhada de recarga de veículos elétricos, administrar consumo por usuário, alocar custos e antecipar situações de atenção pode ser difícil. O EV ChargeOps registra sessões, calcula rateio individual por kWh e exibe informações de inteligência operacional para responsáveis pela infraestrutura.

O projeto considera como referência o carregador **GoodWe HCA G2**, instalado no estacionamento L1 da FIAP Aclimação, conforme o desafio. O projeto **não possui acesso ao HCA G2 nem à plataforma GoodWe/SEMS+**; as entradas são manuais ou geradas por simulador reproduzível.

A **Sprint 1** definiu arquitetura e proposta. A **Sprint 2** implementa backend, persistência, IA e dashboard React conectado aos endpoints, com código e evidências de execução.

## 2. O que foi implementado

| Entrega | Como funciona | Onde encontrar |
|---|---|---|
| API de sessões | Lista usuários/carregadores, cria e consulta sessões, rejeita IDs repetidos, horários inválidos e conflito no carregador | `backend/app/main.py` |
| Persistência | SQLAlchemy com PostgreSQL como configuração padrão; SQLite para testes/demo local | `backend/app/database.py`, `models.py`, `docker-compose.sprint2.yml` |
| Rateio mensal | Soma kWh válidos por usuário, aplica tarifa e taxa fixa somente a usuário com consumo faturável | `backend/app/billing.py`, `GET /api/invoices` |
| Previsão de demanda | RandomForestRegressor com dados históricos diários e validação cronológica versus média móvel de 7 dias | `backend/app/intelligence.py` |
| Detecção de anomalias | IsolationForest em sessões validadas; scores e indicadores descritivos | `backend/app/intelligence.py` |
| Recomendações | Regras ligadas aos resultados dos modelos, pedindo revisão humana quando necessário | `GET /api/ai/recommendations` |
| Dashboard React | Visão geral, sessões, rateio e inteligência artificial; envia novos registros à API | `frontend/index.html`, `frontend/js/app.js` |
| Testes e evidências | Testes de negócio, IA e integração; capturas da interface; JSON com respostas reais da API | `backend/tests/`, `docs/sprint-02/evidencias/` |

**Não foram implementados:** login e permissões reais, integração GoodWe/SEMS+, pagamentos, acionamento remoto do carregador, emissão fiscal e sistema de cobrança persistente. Esses itens requerem infraestrutura e testes de segurança adicionais.

## 3. Execução rápida — Windows (mais simples)

Requer Python **3.11 ou superior**, navegador e internet para a primeira instalação das dependências Python.

1. Baixe o repositório, extraia (caso esteja compactado) e abra a pasta principal.
2. Dê dois cliques em **`INICIAR_DEMO_WINDOWS.bat`**.
3. Aguarde a instalação inicial, criação da base fictícia e abertura do navegador.
4. Acesse **http://127.0.0.1:5173/**. A documentação da API fica em **http://127.0.0.1:8000/docs**.
5. Para encerrar, feche as duas janelas de terminal que serão abertas (API e servidor de arquivos do frontend).

Essa modalidade inicia **SQLite local**, sem Docker. **Ela não constitui evidência de funcionamento em PostgreSQL**. Para validação da arquitetura prometida na Sprint 1, use a modalidade abaixo.

## 4. Execução com PostgreSQL 16 (arquitetura planejada)

Requer Python 3.11+, Docker Desktop aberto, Docker Compose disponível e acesso às portas locais **5432, 8000 e 5173**.

Abra **`INICIAR_POSTGRES_WINDOWS.bat`** (na primeira vez, Docker baixará a imagem do PostgreSQL). O script instala dependências Python se necessário, sobe o PostgreSQL, cria tabelas, carrega as sessões sintéticas e inicia o backend e o React.

Também pode executar manualmente a partir da raiz do repositório, em PowerShell:

```powershell
docker compose -f docker-compose.sprint2.yml up -d --wait
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://chargeops:chargeops_local@localhost:5432/chargeops"
cd backend
..\.venv\Scripts\python.exe -m app.seed_history
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra um **segundo PowerShell** na raiz do repositório:

```powershell
cd frontend
py -3 -m http.server 5173 --bind 127.0.0.1
```

Depois, abra http://127.0.0.1:5173/. Em caso de conflito de portas, encerre servidores anteriores antes de iniciar outro modo. O arquivo `backend/.env.example` lista parâmetros; o protótipo lê variáveis do ambiente e **não carrega `.env` automaticamente**.

A interface é escrita em **React + ReactDOM UMD 16.0.0**, incluídos localmente e sem npm. É uma decisão de simplificação específica do MVP; em produção, atualizar React, fazer build, implementar autenticação e avaliar segurança. Há crédito/licença em `frontend/vendor/LICENCA_E_VERSAO.txt`.

## 5. Navegação na interface

**Visão geral:** consumo faturável, receita ilustrativa, sessões, pendências, previsão e recomendações.

**Sessões de recarga:** cadastrar usuário, carregador, horário inicial/final, energia medida e situação; consultar histórico. O ID é gerado automaticamente no frontend. Ao salvar, os cálculos do backend e os resultados de IA são consultados novamente. Uma sessão com `falha_comunicacao` permanece não validada e fora do rateio.

**Rateio e faturas:** para o mês selecionado, visualizar detalhamento por usuário (energia, tarifa, manutenção, total e pendências). Os valores da tarifa e da manutenção mostrados no painel são consultados em `/api/config`, sem cifras fixas na interface.

**Inteligência artificial:** verificar MAE, comparação com referência, previsões, sessões atípicas e recomendações resultantes.

## 6. Política de consumo e rateio

A tarifa demonstrativa padrão é **R$ 0,90 por kWh** e a manutenção é **R$ 5,00 por usuário que consumiu energia faturável no mês**. Ambas são configuráveis pelas variáveis de ambiente `TARIFA_KWH` e `MANUTENCAO_MENSAL`, sendo obrigatório usar valores não negativos.

`valor_energia = soma(kWh validados) × tarifa_kWh`

`total_usuario = valor_energia + manutencao_unica` (apenas se houver consumo faturável).

O backend calcula com `Decimal` e arredonda valores monetários a centavos em `billing.py`. Uma sessão é atribuída ao **mês local de São Paulo do seu início**. Sessões interrompidas **validadas** entram com a energia efetivamente medida; falhas de comunicação não validadas ficam pendentes. O sistema não soma energia estimada ou não registrada.

Exemplo com os dados iniciais de **outubro/2026**, antes de inserir novas sessões:

| Usuário | kWh cobrados | Energia | Manutenção | Total | Estado |
|---|---:|---:|---:|---:|---|
| U001 | 18,500 | R$ 16,65 | R$ 5,00 | **R$ 21,65** | calculada |
| U002 | 24,000 | R$ 21,60 | R$ 5,00 | **R$ 26,60** | calculada |
| U003 | 0,000 | R$ 0,00 | R$ 0,00 | **R$ 0,00** | sem consumo |
| U004 | 0,000 | R$ 0,00 | R$ 0,00 | **R$ 0,00** | 1 pendência |

Os totais são dinâmicos e mudam conforme as sessões registradas. **Não há transação financeira real.**

## 7. IA estrutural — fluxo, modelos e limites

Os endpoints de IA e o rateio consultam **a mesma tabela de sessões**. A IA não é um elemento isolado da interface:

1. O usuário cadastra uma sessão no React → `POST /api/sessions` → banco.
2. O rateio (`GET /api/invoices`) considera somente sessões validadas do mês.
3. A previsão (`GET /api/ai/forecast`) reúne sessões validadas por dia local, preenche dias sem consumo, treina Random Forest com variáveis históricas sem o alvo presente e prevê 7 dias.
4. A detecção (`GET /api/ai/anomalies`) treina Isolation Forest para sinalizar comportamentos atípicos nas sessões validadas.
5. As recomendações (`GET /api/ai/recommendations`) combinam resultados desses modelos com regras transparentes de decisão. O React exibe os resultados atualizados.

**Métricas:** o modelo de previsão usa avaliação cronológica de um passo à frente e comparação com a média móvel de 7 dias, reportando MAE. Os valores podem indicar desempenho **inferior** ao baseline — e então o sistema recomenda não automatizar agendamentos. O histórico sintético não comprova desempenho operacional nem capacidade de generalização. O modelo só é executado com histórico mínimo (35 dias para previsão e 25 sessões validadas para anomalias). Os outliers são **estatísticos**, não comprovação de fraude ou defeito.

**Origem:** as 99 sessões sintéticas adicionadas a julho–setembro de 2026 são determinísticas (`backend/app/seed_history.py`). A última data observada define o horizonte de previsão; não é previsão meteorológica nem consumo futuro real. Nenhuma API ou dado privado GoodWe foi acessado.

## 8. Endpoints principais

| Método | Rota | Resultado |
|---|---|---|
| GET | `/api/health` | status da API |
| GET | `/api/config` | tarifa por kWh e manutenção efetivamente configuradas |
| GET | `/api/users` | catálogo de usuários fictícios |
| GET | `/api/chargers` | carregadores simulados |
| POST | `/api/sessions` | cadastra sessão validada/pendente |
| GET | `/api/sessions` | lista sessões; permite `?period=AAAA-MM` |
| GET | `/api/invoices?period=2026-10` | rateio mensal |
| GET | `/api/ai/forecast` | demanda e métricas |
| GET | `/api/ai/anomalies` | scores e sinais estatísticos |
| GET | `/api/ai/recommendations` | recomendações rastreáveis |

Swagger interativo: http://127.0.0.1:8000/docs.

## Evidências visuais e verificação para a banca

As cinco capturas abaixo representam o dashboard React executado com respostas da API FastAPI e um banco SQLite de demonstração. O código completo, os testes e o JSON com resultados reproduzíveis estão no repositório.

![Visão geral EV ChargeOps](docs/sprint-02/evidencias/01-dashboard.webp)

| Tela | Evidência |
|---|---|
| Visão geral | [Dashboard](docs/sprint-02/evidencias/01-dashboard.webp) |
| Sessões | [Registro e histórico](docs/sprint-02/evidencias/02-sessoes.webp) |
| Rateio | [Cobrança individual e tarifa](docs/sprint-02/evidencias/03-rateio.webp) |
| IA | [Previsões, anomalias e recomendações](docs/sprint-02/evidencias/04-inteligencia-artificial.webp) |
| Cadastro | [Sessão cadastrada e confirmada](docs/sprint-02/evidencias/05-cadastro-confirmado.webp) |

**Apresentação técnica:** [Guia do pitch de 5 minutos, demonstração e perguntas da banca](docs/sprint-02/guia_pitch_5_min.md).

**Evidências reproduzíveis:** [28 testes automatizados](docs/sprint-02/evidencias/resultados_testes_finais.txt) · [saída da demonstração](docs/sprint-02/evidencias/saida_demo.txt) · [dados JSON de IA](docs/sprint-02/evidencias/ia_resultados_demo.json) · [decisões e diferenças da Sprint 1](docs/sprint-02/decisoes_finais.md).

## Rastreabilidade da rubrica — Sprint 2

| Critério FIAP | Como verificar | Limitação declarada |
|---|---|---|
| Lógica central (3,0) | `backend/app/main.py` e `billing.py`; `POST /api/sessions`; `GET /api/invoices`; testes de API/rateio | Sessões simuladas; faturas sob demanda |
| IA estrutural (3,0) | `backend/app/intelligence.py`; três endpoints de IA; painel e `test_ai.py` | Dados sintéticos; desempenho não garante uso real |
| Evidências (2,0) | Imagens acima, JSON e resultados dos testes; roteiro de execução | Validados com SQLite, não com PostgreSQL real |
| Autoria e compreensão (1,0) | Regras documentadas, módulos pequenos e testes de cenário | Explicação oral no pitch individual |
| README e GitHub (1,0) | Este README, diagramas da Sprint 1, documentação Sprint 2 e commits | Sem autenticação ou integração SEMS+ física |

## 9. Como testar e comprovar

A partir de `backend/` e com Python/demais dependências instalados:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m app.demo_ia --saida ..\docs\sprint-02\evidencias\ia_resultados_demo.json
```

O teste rápido de IA **usa SQLite isolado e TestClient**. Os testes cobrem rateio, validações, cronologia, anomalias, integração e CORS. Os resultados desta versão estão em `docs/sprint-02/evidencias/resultados_testes_finais.txt`. Também há capturas em WebP do dashboard, cadastro, rateio e IA em `docs/sprint-02/evidencias/`.

**Sobre as capturas:** foram obtidas executando React num navegador automatizado com respostas do FastAPI realmente executado sobre SQLite; a navegação de rede direta foi intermediada por ponte de teste devido a restrições do navegador da infraestrutura. Essas imagens representam a interface em execução, **não comprovam** que PostgreSQL ou o navegador do Windows foram testados. Fazer a verificação local na modalidade PostgreSQL antes da entrega.

## 10. Estrutura

```text
README.md                         documentação final
INICIAR_DEMO_WINDOWS.bat          execução rápida SQLite
INICIAR_POSTGRES_WINDOWS.bat      execução PostgreSQL/Docker
docker-compose.sprint2.yml        PostgreSQL 16
backend/app/                     API, banco, rateio, IA, gerador de dados
backend/tests/                   testes automatizados
backend/requirements.txt         dependências Python
frontend/index.html              aplicação React
frontend/js/app.js               telas, formulário, integração HTTP
frontend/css/style.css           visual do dashboard
frontend/vendor/                 bibliotecas React locais e licença
docs/sprint-02/                  decisões e evidências
entrega_sprint_02.txt             link para o repositório (após publicar)
```

**Continuidade com a Sprint 1:** os diagramas originais permanecem em `docs/`, enquanto uma cópia integral do README original está em `docs/sprint-01/README_original_Sprint01.md`. Consulte `docs/sprint-02/decisoes_finais.md` para justificativas de escopo e desvios.

## 11. Avaliação, limites e melhorias

- Lógica de sessões, rateio, IA integrada e interface funcional com dados sintéticos.
- Sem autenticação/autorização; somente execução local e usuários fictícios.
- React 16.0.0 é obsoleto para produção; atualizar antes de qualquer implantação em rede.
- PostgreSQL é a arquitetura padrão, mas neste ambiente a execução e as imagens foram verificadas com SQLite. A validação PostgreSQL precisa ocorrer no computador com Docker.
- Sem integração GoodWe/SEMS+, carregador físico, gateway fiscal, meios de pagamento ou faturas persistidas.
- Próximos passos para produto real: importação autenticada do carregador, proteção de dados, auditoria de sessões, tarifação temporal, autorização multiusuário, testes em PostgreSQL e validação da qualidade preditiva com séries reais.

**Entregável FIAP ON:** enviar **um arquivo `.TXT` contendo o link do repositório atualizado**. A submissão do `.TXT` deve acontecer **depois** que todos os arquivos forem publicados no GitHub e verificados. Conforme o enunciado, cada estudante deverá gravar seu pitch individual de cinco minutos na avaliação presencial obrigatória.


---

# Anexo — Registro original completo da Sprint 1

O texto a seguir foi preservado para rastreabilidade histórica. A versão original também está disponível em [docs/sprint-01/README_original_Sprint01.md](docs/sprint-01/README_original_Sprint01.md).

# Enterprise Challenge 2026 – EV ChargeOps

## Sprint 01 – Pesquisa e Documentação

## Grupo 20

**Integrante:** Luiz Lucas Guimarães
**RM:** RM574169

---

# 1. Introdução

A mobilidade elétrica vem apresentando crescimento acelerado no Brasil e no mundo. O aumento da frota de veículos elétricos tem impulsionado a expansão da infraestrutura de recarga, criando novas oportunidades e desafios para condomínios residenciais, edifícios corporativos, estacionamentos e instituições de ensino.

Nesse contexto, o compartilhamento de carregadores torna-se uma alternativa economicamente viável, pois reduz custos de instalação e permite melhor aproveitamento dos equipamentos. Entretanto, essa modalidade também gera dificuldades relacionadas à identificação dos usuários, ao controle do consumo energético e à distribuição justa dos custos de utilização.

O desafio proposto pela GoodWe consiste em transformar os dados gerados pelas sessões de recarga em informações capazes de apoiar a gestão da infraestrutura compartilhada. Para atender essa necessidade, o Grupo 20 propõe o desenvolvimento do **EV ChargeOps**, uma plataforma destinada ao gerenciamento de sessões de recarga, cálculo de consumo individual, geração de faturas e apoio à tomada de decisão por meio da análise dos dados coletados.

Este documento apresenta o resultado da Sprint 01 do Enterprise Challenge 2026, contemplando as pesquisas realizadas, as decisões arquiteturais adotadas e o planejamento para a Sprint 02.

---

# 2. Contexto do Problema

## Crescimento da Mobilidade Elétrica

O mercado de veículos eletrificados vem registrando crescimento expressivo nos últimos anos. Segundo dados da Associação Brasileira do Veículo Elétrico (ABVE), o Brasil alcançou recordes consecutivos de comercialização de veículos eletrificados, ampliando significativamente a frota em circulação.

Paralelamente, a infraestrutura de recarga também apresentou expansão relevante, com aumento do número de eletropostos públicos e semipúblicos distribuídos pelo território nacional.

Esse cenário demonstra que a mobilidade elétrica deixou de representar uma tendência futura e passou a constituir uma realidade crescente para consumidores, empresas e instituições.

---

## O Problema da Recarga Compartilhada

Embora a expansão da infraestrutura seja fundamental para o desenvolvimento do setor, a simples instalação de carregadores não resolve todos os desafios operacionais associados à utilização compartilhada dos equipamentos.

Em condomínios, empresas e universidades, um mesmo carregador pode ser utilizado por diversos usuários ao longo do dia, tornando necessária a existência de mecanismos capazes de identificar quem utilizou o equipamento, registrar o consumo individual e distribuir os custos de forma transparente.

Sem uma gestão adequada, surgem dificuldades relacionadas ao controle operacional, à cobrança dos usuários e ao planejamento da expansão da infraestrutura.

---

## Principais Desafios em Condomínios Residenciais

Nos condomínios, o principal desafio consiste em associar corretamente cada sessão de recarga ao respectivo morador.

Os problemas mais frequentes incluem:

* dificuldade em identificar quem realizou determinada recarga;
* ausência de histórico consolidado de utilização;
* dúvidas sobre o consumo individual;
* conflitos relacionados à divisão dos custos de energia;
* falta de transparência para síndicos e moradores.

Sem um sistema de controle adequado, torna-se difícil garantir uma cobrança justa e auditável.

---

## Principais Desafios em Empresas

Em ambientes corporativos, os carregadores podem ser utilizados por funcionários, visitantes e veículos da própria organização.

Entre os desafios observados destacam-se:

* controle dos usuários autorizados;
* monitoramento dos custos operacionais;
* geração de relatórios de utilização;
* acompanhamento da ocupação dos carregadores;
* identificação dos períodos de maior demanda.

Essas informações são importantes para o planejamento da infraestrutura e para a tomada de decisões relacionadas à expansão da capacidade de recarga.

---

## Principais Desafios em Universidades

Instituições de ensino apresentam um cenário ainda mais dinâmico devido ao elevado número de usuários potenciais.

Os principais desafios incluem:

* grande volume de usuários compartilhando os equipamentos;
* controle da utilização dos carregadores;
* monitoramento dos horários de pico;
* geração de indicadores de uso;
* organização da disponibilidade dos recursos.

Nesses ambientes, a gestão eficiente depende diretamente da disponibilidade de dados confiáveis e atualizados.

---

## Tendência Futura

O crescimento contínuo da frota de veículos elétricos indica que a demanda por infraestrutura compartilhada tende a aumentar nos próximos anos.

À medida que mais usuários passam a utilizar os mesmos equipamentos, cresce também a necessidade de ferramentas capazes de:

* registrar sessões automaticamente;
* identificar usuários;
* calcular consumos individuais;
* gerar cobranças transparentes;
* produzir relatórios gerenciais;
* apoiar decisões relacionadas à expansão da infraestrutura.

Dessa forma, a gestão da recarga passa a ser tão importante quanto a própria instalação dos carregadores.

---

## Análise do Grupo 20

O Grupo 20 observa que o crescimento da mobilidade elétrica traz desafios que vão além da infraestrutura física de recarga. Embora a instalação dos equipamentos seja fundamental, a gestão do uso compartilhado torna-se cada vez mais relevante à medida que aumenta o número de usuários.

A ausência de mecanismos de identificação, controle de consumo e transparência na cobrança pode gerar conflitos e dificultar a expansão da infraestrutura. Nesse contexto, o EV ChargeOps é proposto como uma plataforma capaz de transformar dados operacionais em informações úteis para gestores e usuários, permitindo controle das sessões, cálculo de rateio, geração de relatórios e apoio à tomada de decisão.

---

# 3. Frente 1 – Contexto e Problema

## 3.1 Infraestruturas de Recarga Compartilhada

Infraestruturas de recarga compartilhada são sistemas nos quais um ou mais carregadores de veículos elétricos são utilizados por múltiplos usuários.

Esse modelo é amplamente empregado em condomínios residenciais, edifícios corporativos, estacionamentos e campus universitários, permitindo a redução dos custos de instalação e melhor aproveitamento dos equipamentos disponíveis.

### Benefícios

* redução do investimento inicial;
* melhor utilização dos carregadores;
* menor necessidade de instalações individuais;
* possibilidade de expansão gradual da infraestrutura.

### Desafios Operacionais

* identificação correta dos usuários;
* controle das sessões de recarga;
* cálculo de consumo individual;
* distribuição dos custos;
* geração de relatórios gerenciais;
* gerenciamento dos horários de pico.

---

## 3.2 Funcionamento de uma Sessão de Recarga

Uma sessão de recarga corresponde ao período compreendido entre a conexão do veículo ao carregador e o encerramento do carregamento.

Fluxo simplificado:

1. Veículo conectado ao carregador;
2. Identificação do usuário;
3. Liberação da recarga;
4. Transferência de energia;
5. Monitoramento da sessão;
6. Encerramento;
7. Registro dos dados.

Durante esse processo, diversas informações são geradas e podem ser utilizadas pela plataforma.

### Dados Produzidos

* identificador da sessão;
* usuário responsável;
* data da utilização;
* horário de início;
* horário de término;
* duração da sessão;
* energia consumida (kWh);
* potência média;
* potência máxima;
* carregador utilizado;
* status final da sessão.

Esses dados constituem a principal fonte de informação utilizada pelo EV ChargeOps.

---

## 3.3 Modelos de Negócio para Recarga Compartilhada

### Recarga Gratuita

O usuário não realiza qualquer pagamento pela energia utilizada.

**Vantagens**

* simplicidade operacional;
* incentivo à adoção dos veículos elétricos.

**Desvantagens**

* custos integralmente assumidos pelo operador;
* risco de utilização excessiva.

---

### Cobrança por kWh

O usuário paga pela quantidade de energia efetivamente consumida.

**Vantagens**

* maior justiça na cobrança;
* relação direta entre consumo e valor pago.

**Desvantagens**

* necessidade de medição precisa do consumo.

---

### Cobrança por Tempo

O usuário paga pelo tempo de utilização do carregador.

**Vantagens**

* incentiva a liberação rápida da vaga.

**Desvantagens**

* nem sempre representa o consumo real de energia.

---

### Assinatura Mensal

O usuário paga um valor fixo periódico.

**Vantagens**

* previsibilidade financeira.

**Desvantagens**

* possibilidade de subsídio cruzado entre usuários.

---

### Rateio Condominial

Os custos são distribuídos entre os usuários de acordo com regras previamente estabelecidas.

**Vantagens**

* adequado para ambientes compartilhados.

**Desvantagens**

* exige transparência e controle detalhado.




## 3.4 Análise de Mercado

Com o objetivo de compreender como o mercado vem enfrentando os desafios relacionados à gestão da recarga compartilhada, foram analisadas três soluções consolidadas no setor: ChargePoint, Wallbox e Zaptec.

---

### ChargePoint

A ChargePoint é uma das maiores plataformas globais de recarga para veículos elétricos, oferecendo soluções para empresas, estacionamentos, condomínios e operadores de infraestrutura.

#### Problema que Resolve

Gerenciamento centralizado de estações de recarga e monitoramento de usuários.

#### Principais Funcionalidades

* monitoramento remoto dos carregadores;
* controle de acesso dos usuários;
* geração de relatórios;
* cobrança de sessões;
* aplicativo para motoristas;
* gerenciamento centralizado.

#### Modelo de Negócio

Venda de hardware e serviços de gestão em nuvem.

#### Limitações

* dependência de ecossistema proprietário;
* custos elevados para pequenas operações;
* menor flexibilidade para customizações específicas.

---

### Wallbox

A Wallbox oferece carregadores inteligentes destinados principalmente a residências e empresas.

#### Problema que Resolve

Simplificação do processo de recarga por meio de equipamentos conectados e gerenciamento remoto.

#### Principais Funcionalidades

* controle via aplicativo;
* monitoramento do consumo;
* agendamento de recargas;
* integração com sistemas energéticos;
* gerenciamento remoto.

#### Modelo de Negócio

Venda de carregadores inteligentes e serviços complementares.

#### Limitações

* foco maior no carregador do que na gestão compartilhada;
* recursos avançados dependem de integrações adicionais.

---

### Zaptec

A Zaptec possui forte atuação em ambientes compartilhados, especialmente condomínios residenciais.

#### Problema que Resolve

Distribuição eficiente da energia entre múltiplos usuários.

#### Principais Funcionalidades

* identificação individual dos usuários;
* monitoramento remoto;
* balanceamento dinâmico de carga;
* gerenciamento centralizado;
* controle de múltiplos carregadores.

#### Modelo de Negócio

Venda de equipamentos e plataforma de gerenciamento.

#### Limitações

* maior complexidade de implantação;
* custos iniciais mais elevados;
* dependência da infraestrutura própria da solução.

---

### Comparação das Soluções

| Critério               | ChargePoint | Wallbox  | Zaptec |
| ---------------------- | ----------- | -------- | ------ |
| Controle de usuários   | Sim         | Parcial  | Sim    |
| Monitoramento remoto   | Sim         | Sim      | Sim    |
| Aplicativo móvel       | Sim         | Sim      | Sim    |
| Cobrança de sessões    | Sim         | Limitada | Sim    |
| Gestão compartilhada   | Sim         | Parcial  | Forte  |
| Balanceamento de carga | Sim         | Sim      | Forte  |
| Foco em condomínios    | Médio       | Baixo    | Alto   |

---

## 3.5 Análise do Grupo 20

A análise das soluções estudadas demonstra que o mercado já possui ferramentas robustas para monitoramento de carregadores e gerenciamento energético.

Entretanto, observou-se uma oportunidade para ampliar a transparência relacionada ao consumo individual, à geração de faturas e à utilização dos dados para apoio à tomada de decisão.

O EV ChargeOps busca aproveitar os dados gerados pelos carregadores para oferecer funcionalidades voltadas ao controle das sessões, cálculo de rateio, geração de cobranças e produção de indicadores gerenciais, complementando capacidades já presentes nas soluções existentes.

---

# 4. Frente 2 – Base Regulatória e Técnica

## 4.1 Resolução Normativa ANEEL nº 1.000/2021

A Resolução Normativa nº 1.000/2021 consolidou as principais regras relacionadas à prestação do serviço público de distribuição de energia elétrica no Brasil.

Além de reunir direitos e deveres dos consumidores e distribuidoras, a regulamentação também estabelece diretrizes relacionadas à infraestrutura de recarga para veículos elétricos.

Para o contexto do EV ChargeOps, essa regulamentação é importante porque reforça a necessidade de controle adequado do consumo energético e de conformidade com os requisitos aplicáveis à operação das instalações elétricas.

### Impactos para o EV ChargeOps

* necessidade de transparência na cobrança;
* registro adequado do consumo energético;
* compatibilidade com os requisitos das distribuidoras;
* suporte à utilização em ambientes compartilhados;
* conformidade com normas aplicáveis à infraestrutura de recarga.

---

## 4.2 Carregador GoodWe HCA G2

O GoodWe HCA G2 é um carregador inteligente para veículos elétricos projetado para integração com sistemas fotovoltaicos, armazenamento de energia e monitoramento remoto.

Além da recarga convencional, o equipamento pode operar integrado ao ecossistema energético da GoodWe e ser monitorado pela plataforma SEMS+.

---

### Interfaces de Comunicação

#### RFID

Permite identificar usuários por meio de cartões de acesso.

Aplicações:

* autenticação de usuários;
* associação das sessões aos responsáveis;
* controle de acesso ao equipamento.

---

#### Wi-Fi

Permite comunicação do carregador com a internet.

Aplicações:

* envio de dados para a plataforma;
* monitoramento remoto;
* sincronização de informações.

---

#### LAN (Ethernet)

Permite comunicação por rede cabeada.

Aplicações:

* maior estabilidade de conexão;
* operação em ambientes corporativos;
* redução de falhas de comunicação.

---

#### Bluetooth

Permite configuração local do equipamento.

Aplicações:

* instalação inicial;
* manutenção;
* diagnóstico local.

---

#### RS-485

Interface amplamente utilizada em automação industrial.

Aplicações:

* integração com sistemas externos;
* comunicação com controladores;
* expansão futura da solução.

---

## Plataforma SEMS+

O carregador HCA G2 integra-se à plataforma SEMS+, utilizada pela GoodWe para monitoramento e gerenciamento de equipamentos energéticos.

Por meio dessa plataforma é possível:

* monitorar sessões de carregamento;
* acompanhar consumo energético;
* visualizar relatórios;
* programar horários de recarga;
* gerenciar equipamentos conectados.

---

### Dados Relevantes para o EV ChargeOps

Os dados disponibilizados pela infraestrutura GoodWe permitem alimentar os processos centrais da plataforma.

Entre as informações consideradas mais relevantes estão:

| Informação              | Aplicação                    |
| ----------------------- | ---------------------------- |
| Usuário autenticado     | Identificação do responsável |
| Horário de início       | Controle da sessão           |
| Horário de término      | Controle da sessão           |
| Energia consumida (kWh) | Rateio e faturamento         |
| Potência utilizada      | Monitoramento                |
| Status do carregador    | Operação                     |
| Histórico de sessões    | Relatórios                   |
| Eventos de erro         | Diagnóstico                  |

---

## 4.3 APIs Complementares

Além das informações fornecidas pela GoodWe, o EV ChargeOps poderá utilizar APIs externas para enriquecer os dados apresentados aos usuários e gestores.

As APIs analisadas foram a Open Charge Map API e a Google Places API.

---

### Open Charge Map API

A Open Charge Map é uma base global de estações de recarga para veículos elétricos.

#### Dados Selecionados

* localização da estação;
* tipo de conector;
* potência do carregador;
* operador responsável;
* tipo de acesso;
* status operacional.

#### Aplicação no EV ChargeOps

Esses dados poderão auxiliar na visualização da infraestrutura de recarga e na identificação de características técnicas dos equipamentos disponíveis.

---

### Google Places API

A Google Places API fornece informações sobre locais físicos e estabelecimentos.

#### Dados Selecionados

* localização;
* horário de funcionamento;
* avaliações;
* informações do estabelecimento;
* recursos relacionados à recarga elétrica (`evChargeOptions`).

#### Aplicação no EV ChargeOps

Esses dados poderão enriquecer a experiência dos usuários ao fornecer contexto adicional sobre os locais onde a recarga está disponível.

---

### Comparação das APIs

| Critério                    | Open Charge Map           | Google Places       |
| --------------------------- | ------------------------- | ------------------- |
| Foco em mobilidade elétrica | Alto                      | Médio               |
| Dados de carregadores       | Sim                       | Parcial             |
| Dados de localização        | Sim                       | Sim                 |
| Informações comerciais      | Limitadas                 | Amplas              |
| Melhor aplicação            | Infraestrutura de recarga | Contexto geográfico |

---

## 4.4 Análise do Grupo 20

O Grupo 20 conclui que a infraestrutura GoodWe fornece os recursos necessários para coleta dos dados operacionais das sessões de recarga.

Além disso, as APIs analisadas podem complementar a solução ao fornecer informações relacionadas à infraestrutura e ao contexto geográfico dos pontos de recarga.

A combinação dessas fontes permite que o EV ChargeOps utilize dados operacionais, técnicos e contextuais para oferecer uma experiência mais completa para gestores e usuários.



# 5. Frente 3 – Arquitetura e Inteligência

## 5.1 Arquitetura da Solução

O EV ChargeOps foi concebido como uma plataforma de gestão de recarga compartilhada capaz de registrar sessões, calcular consumos individuais, gerar faturamento e fornecer informações para usuários e gestores.

A arquitetura proposta foi organizada em cinco camadas principais.

### Camada Física

Responsável pela interação direta com os veículos elétricos.

Componentes:

* Carregador GoodWe HCA G2;
* Veículos elétricos dos usuários.

Funções:

* fornecimento de energia;
* identificação dos usuários;
* registro inicial das sessões.

---

### Camada de Conectividade

Responsável pela transmissão dos dados gerados durante a recarga.

Componentes:

* Wi-Fi;
* LAN (Ethernet);
* Plataforma SEMS+.

Funções:

* sincronização das informações;
* envio dos dados para a plataforma;
* comunicação entre equipamento e sistema.

---

### Camada de Aplicação

Representa o núcleo da solução.

Funções:

* autenticação dos usuários;
* gerenciamento das sessões;
* cálculo de consumo;
* cálculo do rateio;
* geração de relatórios;
* emissão de faturas.

---

### Camada de Dados

Responsável pelo armazenamento permanente das informações.

Dados armazenados:

* usuários;
* unidades;
* carregadores;
* sessões;
* faturas.

---

### Camada de Inteligência e Apresentação

Responsável pela análise dos dados e disponibilização das informações para os usuários.

Funções:

* previsão de demanda;
* detecção de anomalias;
* recomendações operacionais;
* dashboards para usuários e gestores.

---

### Diagrama de Arquitetura


![Arquitetura EV ChargeOps](docs/arquitetura-ev-chargeops.png)


---

## 5.2 Fluxo dos Dados

O fluxo de dados da plataforma foi definido para garantir rastreabilidade desde o início da sessão até a geração da cobrança.

### Fluxo Operacional

1. Veículo conectado ao carregador;
2. Autenticação do usuário;
3. Início da sessão de recarga;
4. Registro do consumo energético;
5. Encerramento da sessão;
6. Armazenamento dos dados;
7. Cálculo do rateio;
8. Geração da fatura;
9. Exibição das informações no dashboard.

### Transformação dos Dados

#### Dados Brutos

* horário de início;
* horário de término;
* energia consumida;
* potência utilizada.

#### Dados Processados

* consumo mensal;
* custo individual;
* histórico de utilização.

#### Dados Analíticos

* horários de pico;
* padrões de uso;
* recomendações operacionais.

### Diagrama de Fluxo


![Fluxo dos Dados](docs/fluxo-dados.png)


---

## 5.3 Modelo de Rateio

O Grupo 20 optou por um modelo de cobrança baseado no consumo real de energia.

### Variáveis Utilizadas

* consumo energético (kWh);
* tarifa de energia;
* taxa de manutenção da infraestrutura.

### Fórmula Proposta

```text
Valor da Fatura =
(kWh Consumido × Tarifa de Energia)
+ Taxa de Manutenção
```

### Exemplo de Cálculo

Consumo:

* 50 kWh

Tarifa:

* R$ 0,90/kWh

Taxa de manutenção:

* R$ 5,00

Resultado:

```text
(50 × 0,90) + 5,00 = R$ 50,00
```

### Tratamento de Casos Especiais

#### Sessão interrompida

Cobrança apenas do consumo efetivamente registrado.

#### Usuário sem utilização

Não haverá cobrança de consumo.

#### Mais de um veículo

As sessões serão consolidadas para o mesmo usuário.

#### Falha de comunicação

A sessão será encaminhada para análise administrativa.

### Justificativa

O modelo baseado em consumo real foi escolhido por apresentar maior transparência, simplicidade e facilidade de auditoria.

### Diagrama do Rateio


![Modelo de Rateio](docs/modelo-rateio.png)


---

## 5.4 Esquema da Base de Dados

A base de dados foi projetada para garantir rastreabilidade entre usuários, sessões e cobranças.

### Entidades

#### Usuário

* id_usuario
* nome
* email
* tipo_usuario
* id_unidade

#### Unidade

* id_unidade
* bloco
* numero
* responsavel

#### Carregador

* id_carregador
* modelo
* localizacao
* status
* potencia_maxima_kw

#### Sessão de Recarga

* id_sessao
* id_usuario
* id_carregador
* data_inicio
* data_fim
* kwh_consumido
* status_sessao

#### Fatura

* id_fatura
* id_usuario
* mes_referencia
* total_kwh
* valor_energia
* taxa_manutencao
* valor_total
* status_pagamento

---

### Relacionamentos

* Unidade 1 → N Usuários
* Usuário 1 → N Sessões
* Carregador 1 → N Sessões
* Usuário 1 → N Faturas

---

### Exemplos de Registros Simulados

#### Usuários

| ID   | Nome        | Unidade |
| ---- | ----------- | ------- |
| U001 | João Silva  | UN101   |
| U002 | Maria Souza | UN204   |

#### Sessões

| ID   | Usuário | Consumo  |
| ---- | ------- | -------- |
| S001 | U001    | 18,5 kWh |
| S002 | U002    | 24,0 kWh |

#### Faturas

| ID   | Usuário | Valor    |
| ---- | ------- | -------- |
| F001 | U001    | R$ 30,47 |
| F002 | U002    | R$ 26,60 |

### Diagrama ER


![Modelo Entidade-Relacionamento](docs/modelo-er.png)


---

## 5.5 Análise do Grupo 20

O Grupo 20 conclui que uma arquitetura organizada em camadas facilita a manutenção, escalabilidade e evolução da solução. O modelo de rateio baseado em consumo real garante transparência para os usuários, enquanto a estrutura de dados proposta oferece rastreabilidade completa entre sessões e cobranças.

---

# 6. Papel da Inteligência Artificial

A inteligência artificial foi definida como um componente estrutural da solução, atuando diretamente sobre os dados gerados pelas sessões de recarga.

## Previsão de Demanda

Objetivo:

Antecipar períodos de maior utilização da infraestrutura.

Dados utilizados:

* histórico de sessões;
* horários de utilização;
* consumo energético;
* frequência dos usuários.

Benefícios:

* planejamento de expansão;
* identificação de horários de pico.

---

## Detecção de Anomalias

Objetivo:

Identificar comportamentos fora do padrão.

Exemplos:

* consumo excessivo;
* sessões muito longas;
* interrupções frequentes;
* falhas operacionais.

Benefícios:

* identificação rápida de problemas;
* aumento da confiabilidade da operação.

---

## Recomendações Operacionais

Objetivo:

Transformar dados em ações práticas.

Exemplos:

* sugestão de expansão da infraestrutura;
* redistribuição de horários;
* manutenção preventiva;
* revisão de regras operacionais.

---

## Análise do Grupo 20

O Grupo 20 entende que a inteligência artificial deve atuar como uma ferramenta de apoio à decisão e não apenas como um recurso complementar. Sua função é transformar os dados gerados pelas sessões de recarga em conhecimento útil para gestores e usuários.

---

# 7. Plano da Sprint 02

## Objetivo

Desenvolver um protótipo funcional do EV ChargeOps com base nas definições realizadas durante a Sprint 01.

---

## Tecnologias

| Camada         | Tecnologia   |
| -------------- | ------------ |
| Frontend       | React        |
| Backend        | FastAPI      |
| Banco de Dados | PostgreSQL   |
| IA             | Scikit-Learn |
| Diagramas      | Draw.io      |
| Documentação   | Markdown     |

---

## Ordem de Desenvolvimento

### Etapa 1

Modelagem do banco de dados.

### Etapa 2

Desenvolvimento do backend.

### Etapa 3

Cadastro de usuários, unidades e carregadores.

### Etapa 4

Registro das sessões de recarga.

### Etapa 5

Implementação do modelo de rateio.

### Etapa 6

Desenvolvimento do dashboard.

### Etapa 7

Implementação dos módulos de IA.

### Etapa 8

Testes e validação.

---

## Resultado Esperado

Ao final da Sprint 02, espera-se obter um protótipo funcional capaz de registrar sessões, armazenar dados, calcular cobranças individuais e apresentar indicadores para usuários e gestores.

---

# 8. Conclusão

O crescimento da mobilidade elétrica tem ampliado a necessidade de soluções capazes de gerenciar infraestruturas de recarga compartilhadas de forma transparente e eficiente. Ao longo desta pesquisa, o Grupo 20 analisou o contexto do setor, estudou soluções já existentes no mercado, avaliou aspectos regulatórios e definiu uma proposta de arquitetura para o EV ChargeOps.

Os resultados obtidos demonstram que a gestão das sessões de recarga representa um desafio crescente para condomínios, empresas e instituições de ensino. Questões relacionadas à identificação de usuários, controle de consumo e distribuição dos custos exigem mecanismos confiáveis de monitoramento e faturamento.

Como resposta a esse cenário, foi proposta uma plataforma composta por módulos de registro de sessões, cálculo de rateio, armazenamento de dados, geração de faturas e inteligência artificial. A arquitetura definida busca garantir rastreabilidade dos dados, transparência na cobrança e suporte à tomada de decisão.

Além disso, a utilização de inteligência artificial foi planejada como um componente estrutural da solução, atuando na previsão de demanda, detecção de anomalias e geração de recomendações operacionais.

Por fim, a Sprint 01 permitiu consolidar o entendimento do problema, definir a arquitetura da solução e estabelecer as bases para o desenvolvimento da Sprint 02.

---

# 9. Referências

* Associação Brasileira do Veículo Elétrico (ABVE).
* Agência Nacional de Energia Elétrica (ANEEL).
* GOODWE. HCA G2 EV Charger Datasheet.
* GoodWe – Plataforma SEMS+.
* Open Charge Map. API Documentation.
* Google Maps Platform. Places API Documentation.
* ChargePoint.
* Wallbox.
* Zaptec.
* SENATRAN.
* Instituto Brasileiro de Geografia e Estatística (IBGE).
