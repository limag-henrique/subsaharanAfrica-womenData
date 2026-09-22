# Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana (DHS)

## Me baixe!

Siga as instruções abaixo para baixar o repositório ou sincronizar os dados atualizados em sua máquina local:

### 1. Novo Clone (Primeiro Acesso)
```bash
# 1. Clonar o repositório
git clone https://github.com/limag-henrique/subsaharanAfrica-womenData.git
cd subsaharanAfrica-womenData

# 2. Instalar as dependências do ambiente Python
pip install -r requirements.txt
```

### 2. Atualização e Sincronização via Pull (Para quem já clonou anteriormente)
Se você já clonou o repositório antes da consolidação dos dados para CSV, execute a sincronização pull para remover os arquivos brutos pesados e baixar as novas bases consolidadas:

```bash
# Sincronizar o repositório e obter os dados compactados em dados/relevantes/
git pull origin main
```

## Estrutura dos Dados Consolidados (`dados/relevantes`)

A pasta [`dados/relevantes`](dados/relevantes) reúne os microdados estritamente necessários para as entidades e relacionamentos do modelo conceitual, eliminando redundâncias temporais e padronizando identificadores.

### Critério de Construção da Base Comparável
Em vez de somar dados de múltiplas ondas temporais (o que gerava repetições de países e indivíduos entrevistados em anos diferentes), selecionou-se a **onda mais recente e comparável por país** (maior fase DHS). Foram excluídos registros históricos e amostras de teste (como `OS` - África do Sul histórica), resultando na **Base Comparável de 37 Países**.

Todos os arquivos estão em formato CSV comprimido com Gzip (`.csv.gz`) e já incluem colunas padronizadas de rastreabilidade: `pais_codigo`, `pais_nome`, `levantamento_id` (ex: `AO_81`), `fase`, `arquivo_origem`, `linha_origem` e chaves unificadas (`id_mulher_global`, `id_domicilio`, `id_nascimento`, etc.).

### Arquivos Disponíveis

| Arquivo | Recode | Descrição do Conteúdo | Cobertura na Base Comparável | Registros Reais |
| :--- | :---: | :--- | :---: | :---: |
| [`IR.csv.gz`](dados/relevantes/IR.csv.gz) | **IR** | Mulheres entrevistadas (15 a 49 anos): perfil sociodemográfico, fertilidade, contracepção e saúde | 37 países | **407.600** mulheres |
| [`BR.csv.gz`](dados/relevantes/BR.csv.gz) | **BR** | Histórico completo de partos e nascimentos de cada mulher | 37 países | **877.412** nascimentos |
| [`HR.csv.gz`](dados/relevantes/HR.csv.gz) | **HR** | Domicílios: tipo de habitação, bens duráveis, água, esgoto e eletricidade | 36 países | **385.457** domicílios |
| [`PR.csv.gz`](dados/relevantes/PR.csv.gz) | **PR** | Moradores do domicílio: composição demográfica completa | 36 países | **1.884.683** moradores |
| [`KR.csv.gz`](dados/relevantes/KR.csv.gz) | **KR** | Crianças menores de 5 anos: vacinação, aleitamento e episódios de doenças | 37 países | **282.641** crianças |
| [`HW.csv.gz`](dados/relevantes/HW.csv.gz) | **HW** | Antropometria e dosagem de hemoglobina/anemia materna e infantil | 28 países | 2.816 medições diretas |
| [`CR.csv.gz`](dados/relevantes/CR.csv.gz) | **CR** | Casais pareados: entrevistas conjuntas entre cônjuges | 36 países | 67.006 casais |
| [`MR.csv.gz`](dados/relevantes/MR.csv.gz) | **MR** | Homens/parceiros entrevistados em idade reprodutiva | 36 países | 144.714 parceiros |
| [`SQ.csv.gz`](dados/relevantes/SQ.csv.gz) | **SQ** | Infraestrutura comunitária e serviços de saúde locais | 19 países | 6.548 registros |
| [`WI.csv.gz`](dados/relevantes/WI.csv.gz) | **WI** | Índice de riqueza (*wealth index*) adicional do DHS | 26 países | 5.551 registros |

> [!TIP]
> O arquivo [`dados/relevantes/manifesto_selecao.csv`](dados/relevantes/manifesto_selecao.csv) contém o registro de governança completo, detalhando o arquivo de origem, a fase DHS, a contagem de linhas e cada uma das colunas selecionadas em cada país.

---

## Como Carregar os Dados no SQLite (Jupyter Notebook)

Com a consolidação em `.csv.gz`, a carga dos dados no SQLite dentro do notebook oficial `tp_template.ipynb` tornou-se direta:

```python
import sqlite3
import pandas as pd

# Conectar (ou criar) o banco de dados SQLite local
conn = sqlite3.connect("saude_mulher_dhs.db")

# 1. Carregar a tabela de Mulheres (IR)
print("Carregando Mulher (IR)...")
df_mulher = pd.read_csv("dados/relevantes/IR.csv.gz", compression="gzip")
df_mulher.to_sql("Mulher", conn, if_exists="replace", index=False)

# 2. Carregar a tabela de Nascimentos / Gestação e Parto (BR)
print("Carregando Nascimento (BR)...")
df_nascimento = pd.read_csv("dados/relevantes/BR.csv.gz", compression="gzip")
df_nascimento.to_sql("Nascimento", conn, if_exists="replace", index=False)

# 3. Carregar Domicílios (HR)
print("Carregando Domicilio (HR)...")
df_domicilio = pd.read_csv("dados/relevantes/HR.csv.gz", compression="gzip")
df_domicilio.to_sql("Domicilio", conn, if_exists="replace", index=False)

print("Carga concluída com sucesso!")
```

Se desejar inspecionar o script responsável por extrair e gerar os CSVs a partir dos dados brutos originais do DHS, consulte [`database_python/preparar_dados_projeto.py`](database_python/preparar_dados_projeto.py).

---

## Repertório Analítico e Auditorias (`analises` e `analises_completo`)

Para fundamentar as escolhas de modelagem e garantir rigor estatístico, foram realizadas auditorias semânticas sobre o inventário completo do DHS. Os resultados encontram-se documentados e versionados nas pastas [`analises/`](analises) e [`analises_completo/`](analises_completo):

1. **Modelagem e Comparabilidade Continental:**
   - [`analises_completo/tabela_alternativas_modelagem.md`](analises_completo/tabela_alternativas_modelagem.md): Compara o inventário bruto total (1.409 arquivos, 2,13 milhões de mulheres com repetições entre ondas) contra a **Base Comparável Recomendada (37 países e 407.600 mulheres)**, fundamentando a estrutura de entidades e cardinalidades.

2. **Auditoria de Variáveis e Famílias Semânticas:**
   - [`analises_completo/relatorio_entidades_saude_mulher.md`](analises_completo/relatorio_entidades_saude_mulher.md) e [`analises/relatorio_entidades_saude_mulher.md`](analises/relatorio_entidades_saude_mulher.md): Diagnóstico aprofundado dos dicionários de variáveis do DHS. Identificou **559 variáveis com nomes estritamente idênticos** presentes em todos os países comparáveis ([`variaveis_comuns_37_paises.csv`](analises_completo/variaveis_comuns_37_paises.csv)).
   - [`analises_completo/denominacoes_normalizadas.csv`](analises_completo/denominacoes_normalizadas.csv): Mapeamento e desambiguação de rótulos entre diferentes fases e línguas de aplicação dos questionários.
   - [`analises_completo/familias_semanticas.csv`](analises_completo/familias_semanticas.csv): Agrupamento semântico de variáveis por temas de interesse.

3. **Cobertura Temática por Domínio:**
   Conforme detalhado em [`analises_completo/cobertura_temas.csv`](analises_completo/cobertura_temas.csv), as variáveis cobrem 10 grandes dimensões nos 37 países:
   - **História Reprodutiva e Fecundidade:** Fecundidade total, filhos sobreviventes, gravidez atual.
   - **Saúde Materna e Assistência ao Parto:** Pré-natal, assistência qualificada, local de parto.
   - **Planejamento Familiar:** Métodos modernos vs. tradicionais, conhecimento e uso.
   - **Nutrição e Anemia:** Antropometria, hemoglobina materna e infantil.
   - **Condições Socioeconômicas:** Quintil de riqueza, saneamento, acesso a água e luz.
   - **Violência de Gênero e Autonomia:** Presente em 35 dos 37 países (módulo específico de violência doméstica e poder decisório).

---

## Modelo Conceitual e Proposta de Banco de Dados

### 1. Entidades Propostas e Instâncias Reais (Base Comparável)

A auditoria demonstrou a importância crucial de instituir a entidade **`Levantamento`** como dimensão agregadora, prevenindo ambiguidades entre dados de coletas amostrais distintas e mantendo a integridade referencial:

| Entidade | Descrição e Atributos Principais | Chave Primária (PK) / Estrangeira (FK) | Instâncias Reais |
| :--- | :--- | :--- | :---: |
| **`Pais`** | Identificação geopolítica (`nome_pais`, `regiao_africana`) | **PK:** `pais_codigo` (ex: `AO`, `MZ`, `NG`) | **37** países |
| **`Levantamento`** | Rodada de pesquisa DHS realizada (`ano_fase`, `versao_questionario`) | **PK:** `levantamento_id` (ex: `AO_81`)<br>**FK:** `pais_codigo` | **37** levantamentos |
| **`Domicilio`** | Unidade habitacional (`tipo_residencia`: Urbano/Rural, `quintil_riqueza`, `fonte_agua`, `tipo_sanitario`) | **PK:** `id_domicilio`<br>**FK:** `pais_codigo`, `levantamento_id` | **385.457** domicílios |
| **`Mulher`** | Entrevistada (15 a 49 anos) (`idade`, `escolaridade`, `total_filhos`, `idade_primeiro_parto`, `status_anemia`) | **PK:** `id_mulher_global`<br>**FK:** `id_domicilio`, `levantamento_id`, `pais_codigo` | **407.600** mulheres |
| **`Nascimento`** / `Gestacao_Parto` | Registro obstétrico detalhado (`ordem_nascimento`, `consultas_prenatal`, `local_parto`, `parto_assistido`) | **PK:** `id_nascimento`<br>**FK:** `id_mulher_global` | **877.412** nascimentos |
| **`Crianca`** *(Opcional)* | Crianças de 0 a 5 anos (`peso`, `altura`, `vacinacao`, `aleitamento`) | **PK:** `id_crianca`<br>**FK:** `id_mulher_global` | **282.641** crianças |
| **`Metodo_Contraceptivo`** | Catálogo oficial DHS/OMS de métodos contraceptivos (`nome_metodo`, `classificacao`: Moderno/Tradicional/Permanente) | **PK:** `id_metodo` | **18** métodos |

---

### 2. Relacionamentos e Cardinalidades

| Relacionamento | Cardinalidade | Regra de Negócio | Instâncias Reais Comprovadas |
| :--- | :---: | :--- | :---: |
| **`Pertence_A`**<br>(`Domicilio` ➔ `Pais`) | **N : 1** | Cada domicílio amostrado pertence a um país. | **385.457** vínculos |
| **`Realizado_Em`**<br>(`Levantamento` ➔ `Pais`) | **N : 1** | Cada levantamento pertence ao histórico de um país. | **37** vínculos |
| **`Participa_De`**<br>(`Mulher` ➔ `Levantamento`) | **N : 1** | Cada mulher foi entrevistada em um levantamento específico. | **407.600** vínculos |
| **`Reside_Em`**<br>(`Mulher` ➔ `Domicilio`) | **N : 1** | Cada mulher reside em um domicílio cadastrado. | **407.600** vínculos |
| **`Tem_Nascimento`**<br>(`Mulher` ➔ `Nascimento`) | **1 : N** | Uma mulher pode ter múltiplos nascimentos registrados ao longo da vida fértil. | **877.412** vínculos |
| **`Tem_Crianca`**<br>(`Mulher` ➔ `Crianca`) | **1 : N** | Crianças com acompanhamento de saúde vinculadas à mãe respondente. | **282.641** vínculos |
| **`Uso_Contracepcao`**<br>(`Mulher` ⮂ `Metodo_Contraceptivo`) | **N : M** *(Requisito Obrigatório)* | Uma mulher conhece e/ou utiliza múltiplos métodos ao longo do tempo; cada método é utilizado por milhares de mulheres. | Materializado via tabela associativa |

> [!NOTE]
> **Implementação do Relacionamento N:M:**  
> O relacionamento N:M é implementado por meio da tabela associativa `Uso_Contracepcao` (`id_mulher_global`, `id_metodo`), incorporando atributos de histórico como `conhece` (derivado de `v304_*`), `ja_usou` (`v307_*`) e `uso_atual` (`v312`).

---

## Dicionário Prático de Variáveis Selecionadas

As principais variáveis DHS já presentes nos arquivos consolidados em [`dados/relevantes`](dados/relevantes):

### Identificação e Demografia (`IR.csv.gz`, `HR.csv.gz`)
- `pais_codigo` / `levantamento_id`: Identificador soberano e fase da pesquisa.
- `caseid` / `id_mulher_global`: Chave primária da mulher entrevistada.
- `v012`: Idade da mulher (em anos completos, 15–49).
- `v024`: Região/província dentro do país.
- `v025` / `hv025`: Tipo de local de residência (`1 = Urbano`, `2 = Rural`).
- `v106`: Maior nível de escolaridade concluído (`0 = Sem escolaridade`, `1 = Primário`, `2 = Secundário`, `3 = Superior`).
- `v190` / `hv270`: Índice de riqueza do domicílio em quintis (`1 = Mais Pobre` a `5 = Mais Rico`).

### Saúde Materna e Histórico Obstétrico (`BR.csv.gz`)
- `bidx`: Índice do nascimento para a mãe respondente.
- `bord`: Ordem de nascimento da criança.
- `b4`: Sexo da criança (`1 = Masculino`, `2 = Feminino`).
- `b5`: Sobrevivência da criança (`0 = Falecida`, `1 = Viva`).
- `m14`: Número de consultas de pré-natal durante a gestação.
- `m15`: Local de ocorrência do parto (`10-19 = Domiciliar`, `20-39 = Hospital/Centro de Saúde Público`, `40-49 = Clínica Privada`).
- `m3a` / `m3b`: Parto assistido por médico (`m3a = 1`) ou parteira/enfermeira (`m3b = 1`).

### Contracepção e Planejamento Familiar (`IR.csv.gz`)
- `v312`: Método contraceptivo em uso atual (`0 = Nenhum`, `1 = Pílula`, `2 = DIU`, `3 = Injetável`, `11 = Preservativo masculino`, etc.).
- `v313`: Tipo de método utilizado (`0 = Nenhum`, `1 = Folclórico/Tradicional`, `2 = Moderno`).
- `v301`: Conhecimento geral de qualquer método contraceptivo.

### Indicadores de Nutrição e Saúde da Mulher (`IR.csv.gz`, `HW.csv.gz`)
- `v445`: Índice de Massa Corporal (IMC com 2 decimais implícitas, ex: `2250` = `22.50`).
- `v453`: Nível de hemoglobina corrigido para altitude e tabagismo.
- `v457`: Nível de anemia diagnosticado (`1 = Severa`, `2 = Moderada`, `3 = Leve`, `4 = Não anêmica`).

---

## Perguntas Analíticas e Consultas SQL

As 10 consultas SQL distribuem-se conforme o regulamento do trabalho nas 4 categorias obrigatórias:

### Linhas de Investigação em Saúde Pública
1. **Deserto Pré-natal e Partos Desassistidos:**
   - *Pergunta:* Quais os países com maior proporção de partos domiciliares sem assistência qualificada, e como a escolaridade materna mitiga esse risco?
   - *SQL:* Junção entre `Pais`, `Mulher` e `Nascimento`.
2. **A Crise Silenciosa da Anemia: Abismo Rural vs. Urbano:**
   - *Pergunta:* Qual a prevalência de anemia moderada a severa entre mulheres em idade fértil, e onde a disparidade urbano-rural é mais acentuada?
   - *SQL:* Junção entre `Pais`, `Domicilio` e `Mulher`, agrupando por `tipo_residencia`.
3. **Iniquidade Econômica no Planejamento Familiar Moderno:**
   - *Pergunta:* Qual o gradiente de acesso a contraceptivos modernos entre mulheres do quintil mais rico (5) e do mais pobre (1)?
   - *SQL:* Junção entre `Pais`, `Domicilio`, `Mulher` e `Metodo_Contraceptivo`.

### Categorias das 10 Consultas SQL
- **Seleção e Projeção (2 consultas):** Ex: Filtrar mulheres com mais de 35 anos em áreas rurais; listar partos ocorridos em ambiente domiciliar.
- **Junção de 2 relações (3 consultas):** Ex: Cruzamento `Mulher` ⨝ `Domicilio` para análise de anemia por quintil de riqueza.
- **Junção de 3 ou mais relações (3 consultas):** Ex: `Pais` ⨝ `Mulher` ⨝ `Nascimento` para avaliar médias de consultas pré-natais por região geopolítica.
- **Agregações sobre Junção de 2+ relações (2 consultas):** Ex: `GROUP BY` com funções agregadas (`AVG`, `COUNT`, `HAVING`) calculando taxas de cobertura obstétrica por faixa de renda e país.

---

## Otimização de Consultas (+20% de Pontuação)

Para comprovação do ganho de desempenho via índices:
1. Executar `EXPLAIN QUERY PLAN <consulta>` identificando operações de varredura completa (`SCAN TABLE`).
2. Criar índices adequados nas colunas de filtro ou chave estrangeira:
   ```sql
   CREATE INDEX idx_mulher_idade ON Mulher(v012);
   CREATE INDEX idx_nascimento_mulher ON Nascimento(id_mulher_global);
   ```
3. Executar novamente o plano de execução comprovando o uso do índice (`SEARCH TABLE ... USING INDEX`).
4. Medir e comparar o tempo de execução no Jupyter Notebook utilizando a diretiva `%timeit`.

---

## Calendário de Entregas

| Data | Entrega | Formato | Detalhes |
| :--- | :--- | :--- | :--- |
| **25/09** | **Proposta** | `.pdf` (máx. 1 página) | Tema (Saúde da Mulher na África Subsaariana), descrição do dataset consolidado, entidades e relacionamentos fundamentados na base de 37 países. |
| **23/10** | **Relatório Parcial** | `.ipynb` + `.pdf` | Seções 1 a 5 do template: Título, Membros, Descrição dos Dados, Diagrama ER e Esquema Relacional Normalizado. |
| **23/11** | **Relatório Final** | `.ipynb` + `.pdf` | Projeto completo: 10 consultas SQL executadas e comentadas, testes de otimização com índices e autoavaliação. |
| **23 a 30/11** | **Apresentação** | Slides (máx. 6 min) | Apresentação em grupo sobre a modelagem de dados, arquitetura e achados analíticos. |

