# Graph Report - África Subsaariana  (2026-09-22)

## Corpus Check
- 10 files · ~24,440 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 112 nodes · 142 edges · 10 communities
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
- load_catalog
- 5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)
- Auditoria de entidades e denominações dos dados DHS
- Auditoria de entidades e denominações dos dados DHS
- Alternativas de modelagem: saúde da mulher na África Subsaariana
- DHSApiClient
- carregar_sqlite.py

## God Nodes (most connected - your core abstractions)
1. `DHSDownloader` - 12 edges
2. `load_catalog()` - 8 edges
3. `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` - 8 edges
4. `5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)` - 8 edges
5. `Auditoria de entidades e denominações dos dados DHS` - 8 edges
6. `Auditoria de entidades e denominações dos dados DHS` - 8 edges
7. `main()` - 7 edges
8. `Alternativas de modelagem: saúde da mulher na África Subsaariana` - 7 edges
9. `DHSApiClient` - 6 edges
10. `catalog_stem()` - 5 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Import Cycles
- None detected.

## Communities (10 total, 0 thin omitted)

### Community 0 - "DHSDownloader"
Cohesion: 0.14
Nodes (12): DHSDownloader, main(), Path, Script principal para download e organização dos datasets do DHS Program…, Configura a sessão autenticada com cookies ou login., Extrai CFID e CFTOKEN da URL e salva nos cookies da sessão., Identifica e seleciona o projeto DHS aprovado na sessão ativa., Realiza autenticação no DHS Program via formulário POST e ativa o projeto. (+4 more)

### Community 1 - "Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana"
Cohesion: 0.12
Nodes (15): 1. Visão Geral e Objetivos do Trabalho, 4. Dicionário Prático de Variáveis-Chave do DHS (IR), 6. Calendário de Entregas, Como Processar os Dados e Carregar no SQLite, Direto no Jupyter Notebook, Entendendo os Dados em `dados/brutos`, Identificação e Demografia, Indicadores de Nutrição e Saúde Geral (+7 more)

### Community 2 - "analisar_entidades.py"
Cohesion: 0.35
Nodes (11): catalog_stem(), classify_theme(), collect_metadata(), main(), normalize_text(), Path, Audita metadados dos microdados DHS e produz relatórios de padronização. O…, Converte o nome de pacote DHS (...DT.zip) em stem do arquivo (...FL). (+3 more)

### Community 3 - "load_catalog"
Cohesion: 0.25
Nodes (8): export_catalog_files(), load_catalog(), parse_dhs_url(), Catalogo e mapeamento de metadados dos datasets do DHS Program para a África…, Extrai informações estruturadas de uma URL do DHS Program., Lê um arquivo de URLs ou o catálogo CSV exportado pelo projeto., Exporta o catálogo completo em JSON e CSV para apoiar o trabalho prático., CatalogoTest

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

### Community 8 - "DHSApiClient"
Cohesion: 0.33
Nodes (4): DHSApiClient, Consulta metadados públicos do DHS para validar os ZIPs solicitados. A API…, Acrescenta metadados da API sem impedir o download se ela falhar., Session

### Community 9 - "carregar_sqlite.py"
Cohesion: 0.67
Nodes (3): load_dta_to_sqlite(), main(), Script utilitário para carregar datasets extraídos (.dta - Stata) para um banco…

## Knowledge Gaps
- **39 isolated node(s):** `Me baixe!`, `Direto no Jupyter Notebook`, `O que é o Questionário IR (*Individual Recode*)?`, `Tipos de Arquivos Presentes:`, `Identificação e Demografia` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` connect `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` to `5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `load_catalog()` connect `load_catalog` to `DHSDownloader`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **What connects `Me baixe!`, `Direto no Jupyter Notebook`, `O que é o Questionário IR (*Individual Recode*)?` to the rest of the system?**
  _39 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `DHSDownloader` be split into smaller, more focused modules?**
  _Cohesion score 0.1422924901185771 - nodes in this community are weakly interconnected._
- **Should `Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._