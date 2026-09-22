# Graph Report - África Subsaariana  (2026-09-22)

## Corpus Check
- 11 files · ~13,812 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 130 nodes · 177 edges · 11 communities (10 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bb512f8e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DHSDownloader
- Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana
- analisar_entidades.py
- .run
- 5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)
- Auditoria de entidades e denominações dos dados DHS
- Auditoria de entidades e denominações dos dados DHS
- Alternativas de modelagem: saúde da mulher na África Subsaariana
- preparar_dados_projeto.py
- carregar_sqlite.py
- relevantes/README.md

## God Nodes (most connected - your core abstractions)
1. `DHSDownloader` - 12 edges
2. `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` - 9 edges
3. `load_catalog()` - 8 edges
4. `prepare()` - 8 edges
5. `5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)` - 8 edges
6. `Auditoria de entidades e denominações dos dados DHS` - 8 edges
7. `Auditoria de entidades e denominações dos dados DHS` - 8 edges
8. `main()` - 7 edges
9. `Alternativas de modelagem: saúde da mulher na África Subsaariana` - 7 edges
10. `DHSApiClient` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `DHSDownloader`  [EXTRACTED]
  database_python/baixar_datasets.py → database_python/baixar_datasets.py  _Bridges community 0 → community 3_

## Import Cycles
- None detected.

## Communities (11 total, 1 thin omitted)

### Community 0 - "DHSDownloader"
Cohesion: 0.15
Nodes (10): DHSDownloader, Path, Configura a sessão autenticada com cookies ou login., Extrai CFID e CFTOKEN da URL e salva nos cookies da sessão., Identifica e seleciona o projeto DHS aprovado na sessão ativa., Realiza autenticação no DHS Program via formulário POST e ativa o projeto., Solicita credenciais interativamente se nenhuma foi informada., Baixa um único dataset e o organiza no diretório correspondente. Verifica se é… (+2 more)

### Community 1 - "Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana"
Cohesion: 0.12
Nodes (16): 1. Visão Geral e Objetivos do Trabalho, 4. Dicionário Prático de Variáveis-Chave do DHS (IR), 6. Calendário de Entregas, Como Processar os Dados e Carregar no SQLite, Direto no Jupyter Notebook, Entendendo os Dados em `dados/brutos`, Identificação e Demografia, Indicadores de Nutrição e Saúde Geral (+8 more)

### Community 2 - "analisar_entidades.py"
Cohesion: 0.35
Nodes (11): catalog_stem(), classify_theme(), collect_metadata(), main(), normalize_text(), Path, Audita metadados dos microdados DHS e produz relatórios de padronização. O…, Converte o nome de pacote DHS (...DT.zip) em stem do arquivo (...FL). (+3 more)

### Community 3 - ".run"
Cohesion: 0.14
Nodes (14): DHSApiClient, main(), Script principal para download e organização dos datasets do DHS Program…, Executa a rotina de download e organização com base nos filtros., Consulta metadados públicos do DHS para validar os ZIPs solicitados. A API…, Acrescenta metadados da API sem impedir o download se ela falhar., export_catalog_files(), load_catalog() (+6 more)

### Community 4 - "5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)"
Cohesion: 0.18
Nodes (11): 1. "Deserto Pré-natal e Partos Desassistidos", 1. Entidades Propostas e Número de Instâncias, 2. "A Crise Silenciosa da Anemia: Abismo Rural vs. Urbano", 2. Relacionamentos e Instâncias de cada Relacionamento, 3. Estratégia de Otimização e Carga dos Dados, 3. "Iniquidade Econômica no Planejamento Familiar Moderno", 4. Investigações em Alto Nível: Top 3 Países com Dados Alarmantes, 5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países) (+3 more)

### Community 5 - "Auditoria de entidades e denominações dos dados DHS"
Cohesion: 0.20
Nodes (9): A separação atual está correta?, Artefatos, Auditoria de entidades e denominações dos dados DHS, Entidades canônicas para o modelo relacional, Equivalência semântica, Escopo e método, Núcleo comum de entidades/conceitos, Possibilidade de repetir o download (+1 more)

### Community 6 - "Auditoria de entidades e denominações dos dados DHS"
Cohesion: 0.20
Nodes (9): A separação atual está correta?, Artefatos, Auditoria de entidades e denominações dos dados DHS, Entidades canônicas para o modelo relacional, Equivalência semântica, Escopo e método, Núcleo comum de entidades/conceitos, Possibilidade de repetir o download (+1 more)

### Community 7 - "Alternativas de modelagem: saúde da mulher na África Subsaariana"
Cohesion: 0.25
Nodes (7): Alternativas de escopo para o modelo ER, Alternativas de modelagem: saúde da mulher na África Subsaariana, Contagem bruta por recode, Critério adotado, Decisões importantes para a integração futura, Instâncias dos relacionamentos do modelo recomendado, Recomendação

### Community 8 - "preparar_dados_projeto.py"
Cohesion: 0.31
Nodes (13): add_identifier(), choose_columns(), enrich(), file_parts(), main(), phase_key(), prepare(), Path (+5 more)

### Community 9 - "carregar_sqlite.py"
Cohesion: 0.67
Nodes (3): load_dta_to_sqlite(), main(), Script utilitário para carregar datasets extraídos (.dta - Stata) para um banco…

## Knowledge Gaps
- **41 isolated node(s):** `Me baixe!`, `Direto no Jupyter Notebook`, `Entendendo os Dados em `dados/brutos``, `O que é o Questionário IR (*Individual Recode*)?`, `Tipos de Arquivos Presentes:` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DHSDownloader` connect `DHSDownloader` to `.run`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` connect `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` to `5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **What connects `Me baixe!`, `Direto no Jupyter Notebook`, `Entendendo os Dados em `dados/brutos`` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
- **Should `.run` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._