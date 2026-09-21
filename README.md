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

Como os arquivos `.DTA` possuem milhares de colunas:

### Direto no Jupyter Notebook
Abra o notebook e execute o processamento na **Seção 3**:

```python
import sqlite3
import pandas as pd

# 1. Selecionar apenas as colunas necessárias para as suas entidades
# 2. Ler o arquivo Stata (.DTA) do país escolhido e em contexto unificado
# 3. Conectar ao SQLite e gerar as tabelas do banco
```

---

## Entendendo os Dados em `dados/brutos`

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

## 5. Proposta da Primeira Entrega (25/09) - Escopo Integrado Continental (37 Países)

> **Contexto Macro:** Análise integrada em escala continental cobrindo 37 países da África Subsaariana (população de ~1,3 bilhão, comparável à da China), com base em **503.733 entrevistas individuais** de mulheres em idade reprodutiva coletadas pelo *Demographic and Health Surveys* (DHS).

---

### 1. Entidades Propostas e Número de Instâncias

| Entidade | Descrição e Atributos | Chave Primária (PK) / Estrangeira (FK) | Total de Instâncias Reais |
| :--- | :--- | :--- | :---: |
| **`Pais`** | Identificação geopolítica do país (`nome_pais`, `codigo_iso`, `regiao_africana`: Ocidental, Central, Oriental, Austral) | **PK:** `codigo_pais` (ex: `AO`, `MZ`, `NG`) | **37** países |
| **`Domicilio`** | Unidade habitacional (`tipo_residencia`: Urbano/Rural, `quintil_riqueza`: 1-Muito Pobre a 5-Muito Rico) | **PK:** `id_domicilio` (`codigo_pais` + `cluster` + `household`)<br>**FK:** `codigo_pais` | **~368.000** domicílios |
| **`Mulher`** | Entrevistada em idade reprodutiva (15-49 anos) (`idade`, `escolaridade`, `total_filhos`, `idade_primeiro_parto`, `status_anemia`) | **PK:** `id_mulher` (`caseid` com prefixo do país)<br>**FK:** `id_domicilio` | **503.733** mulheres |
| **`Gestacao_Parto`** | Histórico obstétrico recente dos últimos 5 anos (`consultas_prenatal`, `local_parto`, `parto_assistido_profissional`) | **PK:** `id_gestacao`<br>**FK:** `id_mulher` | **~208.000** partos/gestações |
| **`Metodo_Contraceptivo`** | Catálogo oficial de métodos anticoncepcionais do DHS/OMS (`nome_metodo`, `classificacao`: Moderno/Tradicional/Permanente) | **PK:** `id_metodo` | **18** métodos |

---

### 2. Relacionamentos e Instâncias de cada Relacionamento

| Relacionamento | Cardinalidade | Regra de Negócio | Total de Instâncias |
| :--- | :---: | :--- | :---: |
| **`Pertence_A`**<br>(`Domicilio` ➔ `Pais`) | **N : 1** | Cada domicílio pertence a um país soberano; cada país tem milhares de domicílios amostrados. | **~368.000** associações |
| **`Reside_Em`**<br>(`Mulher` ➔ `Domicilio`) | **N : 1** | Cada mulher reside em um domicílio específico. | **503.733** associações |
| **`Teve_Gestacao`**<br>(`Mulher` ➔ `Gestacao_Parto`) | **1 : N** | Uma mulher pode ter registrado partos recentes (últimos 5 anos). | **~208.000** associações |
| **`Uso_Contracepcao`**<br>(`Mulher` ⮂ `Metodo_Contraceptivo`) | **N : M** *(Requisito Obrigatório)* | Uma mulher pode usar/conhecer vários métodos contraceptivos; cada método é adotado por milhares de mulheres. | **~118.000** associações ativas |

> **Implementação do Relacionamento N:M:** No banco físico relacional, esse relacionamento é materializado na tabela associativa `Uso_Contracepcao` (composta pelas chaves `id_mulher` e `id_metodo`, além de atributos como `uso_atual` e `conhece`).

---

### 3. Estratégia de Otimização e Carga dos Dados

> **Otimização:** Os arquivos `.DTA` de 37 países contêm mais de 7.000 colunas cada (dezenas de gigabytes brutos). Se tentar carregar tudo na memória, o Python travará. O segredo é fazer um loop em Python que carrega apenas as 12-14 colunas de interesse (ex: `caseid`, `v001`, `v002`, `v012`, `v025`, `v106`, `v190`, `v201`, `v212`, `v312`, `m14_1`, `m15_1`, `v457`). Ao carregar apenas essas variáveis, o banco de dados SQLite consolidado terá em torno de **80 MB a 120 MB**, operando de forma ultrarrápida no SQLite com consultas que rodam em frações de segundo.

---

### 4. Investigações em Alto Nível: Top 3 Países com Dados Alarmantes

#### 1. "Deserto Pré-natal e Partos Desassistidos"
* **Pergunta:** Quais os 3 países com maior proporção de partos domiciliares sem assistência médica, e qual a correlação com a escolaridade materna?
* **Lógica SQL:** Junção entre `Pais`, `Mulher` e `Gestacao_Parto`. Filtrar partos onde `local_parto` é domiciliar e agrupar por `Pais` calculando a porcentagem de partos não assistidos (`COUNT(*) * 100.0 / TOTAL`).
* **Hipótese:** Países da região do Sahel (ex: Chade, Níger, Mali) apresentam taxas superiores a 60% de partos domiciliares sem profissional capacitado.

#### 2. "A Crise Silenciosa da Anemia: Abismo Rural vs. Urbano"
* **Pergunta:** Qual a prevalência de anemia moderada a severa entre mulheres em idade fértil, e quais os 3 países onde a desigualdade entre zonas rurais e urbanas é mais crítica?
* **Lógica SQL:** Junção entre `Pais`, `Domicilio` e `Mulher`. Calcular a taxa de anemia (`v457 IN (1, 2)`) agrupada por país e tipo de residência (`Urbano` vs `Rural`).
* **Hipótese:** No meio rural, o isolamento geográfico e a insegurança alimentar elevam a taxa de anemia a níveis de emergência nutricional pública.

#### 3. "Iniquidade Econômica no Planejamento Familiar Moderno"
* **Pergunta:** Quais os 3 países com o maior abismo de acesso a métodos contraceptivos modernos entre as mulheres mais ricas (quintil 5) e as mais pobres (quintil 1)?
* **Lógica SQL:** Junção de 4 tabelas (`Pais`, `Domicilio`, `Mulher`, `Uso_Contracepcao` e `Metodo_Contraceptivo`). Calcular a diferença percentual de uso de métodos modernos entre o quintil 1 e o quintil 5.
* **Hipótese:** Mulheres em situação de extrema vulnerabilidade têm taxa de cobertura inferior a 10%, contra mais de 45% entre mulheres de maior renda.

---

### Carga no SQLite e Jupyter Notebook

No arquivo `tp_template.ipynb` (Seção 3), você implementará o carregamento via Python. 

Exemplo prático de extração filtrada e carga:

```python
import sqlite3
import pandas as pd

# Conectar ao banco SQLite
# Carregar apenas as colunas desejadas do arquivo .DTA
# Criar tabela Mulher
# Inserir no SQLite
```

---

### As 10 Consultas SQL

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

### Otimização de Consultas (+20% Extra)

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
