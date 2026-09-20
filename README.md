# Projeto: Análise de Dados de Saúde da Mulher na África Subsaariana

## Me baixe!

```bash
# 1. Clonar o repositório
git clone https://github.com/limag-henrique/subsaharanAfrica-womenData.git
cd subsaharanAfrica-womenData

# 2. Baixar os microdados de saúde (arquivos .DTA via Git LFS)
git lfs pull

# 3. Instalar as dependências
pip install -r requirements.txt
```

---

## Como Processar os Dados e Carregar no SQLite

Como os arquivos `.DTA` possuem milhares de colunas, processe de forma simples e rápida:

### Opção A: Direto no Jupyter Notebook (`tp_template.ipynb` - Recomendado para a entrega)
Abra o notebook e execute o processamento na **Seção 3**:

```python
import sqlite3
import pandas as pd

# 1. Selecionar apenas as colunas necessárias para as suas entidades
colunas_interesse = [
    'caseid', 'v001', 'v002', 'v012', 'v025', 
    'v106', 'v190', 'v201', 'v212', 'v312', 'm14_1', 'v457'
]

# 2. Ler o arquivo Stata (.DTA) do país escolhido (ex: Angola)
df = pd.read_stata(
    "dados/brutos/Angola/Saude_da_Mulher_IR/AOIR81FL.DTA",
    columns=colunas_interesse,
    convert_categoricals=False
)

# 3. Conectar ao SQLite e gerar as tabelas do banco
conn = sqlite3.connect("saude_africa.db")

# Exemplo: criando a tabela Mulher
df_mulher = df[['caseid', 'v012', 'v106', 'v201', 'v212', 'v457']].copy()
df_mulher.columns = ['id_mulher', 'idade', 'escolaridade', 'total_filhos', 'idade_primeiro_parto', 'status_anemia']
df_mulher.to_sql("Mulher", conn, if_exists="replace", index=False)

print("Tabela Mulher criada com sucesso no SQLite!")
```

### Opção B: Via Script de Linha de Comando
Para carregar um arquivo `.DTA` inteiro ou em lotes para testes:
```bash
python database_python/carregar_sqlite.py "dados/brutos/Angola/Saude_da_Mulher_IR/AOIR81FL.DTA" --db saude_africa.db --table mulheres_angola
```

---

## 1. Visão Geral e Objetivos do Trabalho

O objetivo é projetar e implementar um banco de dados relacional para análise de saúde seguindo um **processo bottom-up**:
1. Partir de uma base não-relacional existente (os microdados brutos do DHS em formato Stata `.dta`).
2. Analisar os dados e **normalizar** o esquema conceitual e relacional.
3. Mapear o esquema normalizado para o **Diagrama ER (Entidade-Relacionamento)**.
4. Inserir os dados processados em um banco **SQLite** manipulado dentro do Jupyter Notebook oficial (`tp_template.ipynb`).
5. Formular e executar **10 consultas analíticas em SQL** e analisar os resultados em saúde pública.

### Requisitos Mínimos Obrigatórios:
- **Pelo menos 4 entidades**, cada uma com ao menos 2 atributos (além da Chave Primária).
- **Pelo menos 3 tipos de relacionamento**, contendo ao menos **1 relacionamento com cardinalidade N:M**.
- **10 consultas SQL** categorizadas rigorosamente conforme a especificação.
- **SGBD**: SQLite embarcado no Jupyter Notebook (`tp_template.ipynb`).

---

## 2. Estrutura do Repositório

```text
África Subsaariana/
├── catalogo_datasets.csv      # Mapeamento de 1.419 datasets com URLs, fases e países
└── dados/
    └── brutos/                # Microdados de 37 países organizados por país
        ├── Angola/
        │   └── Saude_da_Mulher_IR/
        │       ├── AOIR81FL.DTA   # Microdados brutos Stata (pesquisa mais recente)
        │       ├── AOIR81FL.docx  # Questionário e dicionário oficial de variáveis
        │       └── ...
        ├── Mocambique/
        │   └── Saude_da_Mulher_IR/
        │       ├── MZIR62FL.DTA
        │       └── MZIR62FL.DOC
        └── ...
```

---

## 3. Entendendo os Dados em `dados/brutos`

### O que é o Questionário IR (*Individual Recode*)?
O módulo **IR** do DHS é focado exclusivamente em **mulheres em idade fértil (15 a 49 anos)**. É o levantamento mais detalhado sobre saúde reprodutiva e materna do mundo, cobrindo:
- Perfil sociodemográfico (idade, escolaridade, residência urbana/rural, nível de riqueza).
- Histórico completo de partos e nascimentos.
- Pré-natal, assistência ao parto e vacinas maternas (ex: tétano).
- Acesso e uso de métodos contraceptivos.
- Indicadores antropométricos e de saúde (anemia, IMC, peso, altura).

### Tipos de Arquivos Presentes:
| Extensão | Função no Trabalho |
| :--- | :--- |
| **`.DTA`** | **Arquivo de Microdados (Stata):** É a tabela com os dados brutos de todas as entrevistas. Cada linha representa uma mulher entrevistada. Possui milhares de colunas com as variáveis codificadas. |
| **`.DOC` / `.docx` / `.PDF`** | **Dicionário de Variáveis:** Documento de texto que traduz os nomes codificados das colunas (ex: `v012 = Idade`, `v106 = Nível de escolaridade`, `v201 = Total de filhos`). **Consulte este arquivo para escolher os atributos das suas tabelas!** |

---

## 4. Dicionário Prático de Variáveis-Chave do DHS (IR)

Ao abrir um arquivo `.DTA` (ex: `AOIR81FL.DTA`), as colunas seguem a codificação internacional do DHS. Abaixo estão as variáveis mais recomendadas para compor suas entidades no banco relacional:

### Identificação e Demografia
- `caseid`: Identificador único da mulher entrevistada (Chave Primária ideal).
- `v001`: Número do cluster / conglomerado amostral.
- `v002`: Número do domicílio.
- `v012`: Idade da entrevistada (em anos completos).
- `v024`: Região do país (província/estado).
- `v025`: Tipo de residência (`1 = Urbano`, `2 = Rural`).
- `v106`: Maior nível de escolaridade concluído (`0 = Nenhum`, `1 = Primário`, `2 = Secundário`, `3 = Superior`).
- `v190`: Índice de riqueza do domicílio (`1 = Muito Pobre`, `2 = Pobre`, `3 = Médio`, `4 = Rico`, `5 = Muito Rico`).

### Saúde Materna e Reprodutiva
- `v201`: Total de nascidos vivos (número de filhos que teve ao longo da vida).
- `v212`: Idade que a mulher tinha quando deu à luz ao primeiro filho.
- `v312`: Método contraceptivo em uso atual (`0 = Nenhum`, `1 = Pílula`, `2 = DIU`, `3 = Injetável`, etc.).
- `v313`: Tipo de método contraceptivo (`0 = Nenhum`, `1 = Tradicional`, `2 = Moderno`).

### Pré-natal e Assistência ao Parto (Último Filho)
- `m14_1`: Número de consultas pré-natais realizadas durante a gravidez.
- `m15_1`: Local de realização do parto (`10-19 = Domiciliar`, `20-39 = Hospital/Clínica Pública`, `40-49 = Clínica Privada`).
- `m3a_1`: Parto assistido por médico (`0 = Não`, `1 = Sim`).
- `m3b_1`: Parto assistido por enfermeira/parteira (`0 = Não`, `1 = Sim`).

### Indicadores de Nutrição e Saúde Geral
- `v445`: Índice de Massa Corporal (IMC com 2 casas decimais implícitas, ex: 2250 = 22.50).
- `v453`: Nível de hemoglobina ajustado (diagnóstico de anemia).
- `v457`: Nível de anemia (`1 = Severa`, `2 = Moderada`, `3 = Leve`, `4 = Não anêmica`).

---

## 5. Guia Passo a Passo da Metodologia Bottom-Up

### Passo 1: Seleção do Escopo
Recomenda-se escolher **um país principal** com dados recentes (ex: **Angola** - arquivo `dados/brutos/Angola/Saude_da_Mulher_IR/AOIR81FL.DTA` - DHS Fase 8) ou combinar 2 a 3 países de língua portuguesa/regiões próximas (ex: Angola e Moçambique).

---

### Passo 2: Normalização e Atendimento aos Requisitos

No arquivo `.DTA`, todas as variáveis vêm em uma única tabela gigantesca ("não-normalizada"). O objetivo principal da disciplina é realizar a **decomposição e normalização (1FN, 2FN, 3FN)**.

#### Proposta de Esquema Relacional com 4+ Entidades e Relacionamento N:M:

1. **`Pais`** (Dimensão geográfica/institucional):
   - `codigo_pais` (PK, VARCHAR)
   - `nome_pais` (VARCHAR)
   - `regiao_geografica` (VARCHAR)

2. **`Domicilio`** (Condições do lar):
   - `id_domicilio` (PK, VARCHAR gerado por `v001_v002`)
   - `codigo_pais` (FK referenciando `Pais`)
   - `tipo_residencia` (VARCHAR: Urbano / Rural)
   - `quintil_riqueza` (VARCHAR: Muito Pobre a Muito Rico)

3. **`Mulher`** (Dados individuais da entrevistada):
   - `id_mulher` (PK, VARCHAR gerado por `caseid`)
   - `id_domicilio` (FK referenciando `Domicilio`)
   - `idade` (INTEGER)
   - `escolaridade` (VARCHAR)
   - `total_filhos` (INTEGER)
   - `idade_primeiro_parto` (INTEGER)
   - `status_anemia` (VARCHAR)

4. **`Gestacao_Parto`** (Histórico de maternidade - relação 1:N com Mulher):
   - `id_gestacao` (PK, INTEGER AUTOINCREMENT)
   - `id_mulher` (FK referenciando `Mulher`)
   - `consultas_prenatal` (INTEGER)
   - `local_parto` (VARCHAR: Hospital, Posto de Saúde, Casa)
   - `parto_assistido_profissional` (BOOLEAN)

5. **`Metodo_Contraceptivo`** e **`Mulher_Metodo`** (Relacionamento N:M!):
   - **`Metodo_Contraceptivo`**:
     - `id_metodo` (PK, INTEGER)
     - `nome_metodo` (VARCHAR: Pílula, DIU, Camisinha, Injetável, etc.)
     - `classificacao` (VARCHAR: Moderno, Tradicional, Permanente)
   - **`Uso_Contracepcao` (Tabela Associativa N:M)**:
     - `id_mulher` (PK, FK referenciando `Mulher`)
     - `id_metodo` (PK, FK referenciando `Metodo_Contraceptivo`)
     - `uso_atual` (BOOLEAN)
     - `conhecimento_previo` (BOOLEAN)

> Esse arranjo atende **100% dos critérios do professor**: 5 entidades, 4 relacionamentos, e cardinalidade N:M explícita na associação entre Mulheres e Métodos de Saúde/Contracepção.

---

### Passo 3: Carga no SQLite e Jupyter Notebook

No arquivo `tp_template.ipynb` (Seção 3), você implementará o carregamento via Python. 

Exemplo prático de extração filtrada e carga:

```python
import sqlite3
import pandas as pd

# Conectar ao banco SQLite
conn = sqlite3.connect("saude_africa.db")

# Carregar apenas as colunas desejadas do arquivo .DTA
cols_desejadas = [
    'caseid', 'v000', 'v001', 'v002', 'v012', 'v025', 
    'v106', 'v190', 'v201', 'v212', 'v312', 'm14_1', 'm15_1', 'v457'
]

df_raw = pd.read_stata(
    "dados/brutos/Angola/Saude_da_Mulher_IR/AOIR81FL.DTA",
    columns=cols_desejadas,
    convert_categoricals=False
)

# Criar tabela Mulher
df_mulher = df_raw[['caseid', 'v001', 'v002', 'v012', 'v106', 'v201', 'v212', 'v457']].copy()
df_mulher.columns = ['id_mulher', 'cluster', 'num_domicilio', 'idade', 'escolaridade', 'total_filhos', 'idade_primeiro_parto', 'status_anemia']

# Inserir no SQLite
df_mulher.to_sql("Mulher", conn, if_exists="replace", index=False)
```

---

### Passo 4: As 10 Consultas SQL

O trabalho exige exatamente 10 consultas divididas nas 4 categorias da Seção 6 do template:

1. **Seleção e Projeção (2 consultas):**
   - *Exemplo:* Listar mulheres com mais de 30 anos residentes em áreas rurais.
2. **Junção de 2 relações (3 consultas):**
   - *Exemplo:* Cruzar a tabela `Mulher` com `Domicilio` para ver a distribuição de partos por quintil de riqueza.
3. **Junção de 3 ou mais relações (3 consultas):**
   - *Exemplo:* Relacionar `Pais`, `Mulher` e `Gestacao_Parto` para analisar se a média de consultas pré-natais varia entre países ou níveis de escolaridade.
4. **Agregações sobre Junção de 2+ relações (2 consultas):**
   - *Exemplo:* Calcular a média de filhos e percentual de partos hospitalares agrupados por faixa de renda e nível de escolaridade (`COUNT`, `AVG`, `GROUP BY`, `HAVING`).

---

### Passo 5: Otimização de Consultas (+20% Extra)

Para garantir a pontuação extra de otimização:
1. Identifique uma consulta com junção ou filtros frequentes (ex: filtro por `idade` ou `id_domicilio`).
2. Execute o comando `EXPLAIN QUERY PLAN <sua_consulta>;` e observe o scan completo (`SCAN TABLE`).
3. Crie um índice:
   ```sql
   CREATE INDEX idx_mulher_idade ON Mulher(idade);
   ```
4. Execute novamente o `EXPLAIN QUERY PLAN` e comprove que o SQLite passou a utilizar o índice (`SEARCH TABLE ... USING INDEX`).
5. Mostre o ganho de tempo de execução no notebook utilizando `%timeit`.

---

## 6. Calendário de Entregas

| Data | Entrega | Formato | Detalhes |
| :--- | :--- | :--- | :--- |
| **25/09** | **Proposta** | `.pdf` (máx. 1 página) | Grupo, tema escolhido (Saúde da Mulher na África Subsaariana), descrição do dataset, entidades e relacionamentos preliminares. |
| **23/10** | **Relatório Parcial** | `.ipynb` + `.pdf` | Seções 1 a 5 do template: Título, Membros, Descrição dos Dados, Diagrama ER e Diagrama Relacional. |
| **23/11** | **Relatório Final** | `.ipynb` + `.pdf` | Todas as seções completas, incluindo as 10 consultas SQL executadas, otimização e autoavaliação. |
| **23 a 30/11** | **Apresentação** | Slides (máx. 6 min) | Apresentação em grupo sobre a modelagem e as conclusões analíticas. |
