# Análise de Dados de Saúde da Mulher na África Subsaariana (DHS)

## Me baixe!

```bash
# 1. Clonar o repositório
git clone https://github.com/limag-henrique/subsaharanAfrica-womenData.git
cd subsaharanAfrica-womenData

# 2. Descompactar os bancos e CSVs grandes (Python 3.11 ou superior)
python scripts/restaurar_arquivos.py

# 3. Instalar dependências
pip install -r requirements.txt
```

### Como descompactar

Execute `python scripts/restaurar_arquivos.py` na raiz do projeto, no Windows, Linux ou macOS (use `python3` se necessário).

Reserve cerca de **3 GiB livres** para os arquivos restaurados e os temporários.

#### Atualização e Sincronização via Pull (Para quem já clonou)
```bash
git pull origin main
```

#### Visualizador web Python/Flask
```bash
cd database_python
python server.py
```
Acesse no navegador: **[http://localhost:5050](http://localhost:5050)**

---

## Tabelas do Banco de Dados (`saude_mulher_dhs.db`)
| Tabela SQL | Recode | Descrição | Registros | Cobertura |
| :--- | :---: | :--- | ---: | :---: |
| **`Mulher`** | IR | Mulheres de 15 a 49 anos (perfil sociodemográfico, fertilidade, saúde) | 407.600 | 37 países |
| **`Nascimento`** | BR | Histórico de gestações e partos de cada mulher | 877.412 | 27 países |
| **`Domicilio`** | HR | Habitação, saneamento, água, eletricidade e bens | 385.457 | 36 países |
| **`Morador`** | PR | Composição demográfica completa dos domicílios | 1.884.683 | 35 países |
| **`Crianca`** | KR | Crianças menores de 5 anos (saúde, vacinação, nutrição) | 282.641 | 36 países |
| **`Parceiro`** | MR | Homens/parceiros entrevistados em idade reprodutiva | 236.070 | 36 países |
| **`Indice_Riqueza`** | WI | Escala e pontuação de riqueza (*wealth index*) | 190.832 | 26 países |
| **`Antropometria`** | HW | Medições de altura, peso e níveis de hemoglobina/anemia | 150.700 | 28 países |
| **`Casal`** | CR | Entrevistas conjuntas pareadas entre cônjuges | 109.174 | 36 países |
| **`Servico_Comunidade`** | SQ | Infraestrutura comunitária e serviços de saúde locais | 5.154 | 19 países |

> Os dados brutos estão em [`dados/relevantes/`](dados/relevantes/):

| Arquivo | Recode | Descrição do Conteúdo | Cobertura na Base Comparável | Registros Reais |
| :--- | :---: | :--- | :---: | :---: |
| [`IR.csv.gz`](dados/relevantes/IR.csv.gz) | **IR** | Mulheres entrevistadas (15 a 49 anos): perfil sociodemográfico, fertilidade, contracepção e saúde | 37 países | **407.600** mulheres |
| [`BR.csv.gz`](dados/relevantes/BR.csv.gz) | **BR** | Histórico completo de partos e nascimentos de cada mulher | 27 países | **877.412** nascimentos |
| [`HR.csv.gz`](dados/relevantes/HR.csv.gz) | **HR** | Domicílios: tipo de habitação, bens duráveis, água, esgoto e eletricidade | 36 países | **385.457** domicílios |
| [`PR.csv.gz`](dados/relevantes/PR.csv.gz) | **PR** | Moradores do domicílio: composição demográfica completa | 35 países | **1.884.683** moradores |
| [`KR.csv.gz`](dados/relevantes/KR.csv.gz) | **KR** | Crianças menores de 5 anos: vacinação, aleitamento e episódios de doenças | 36 países | **282.641** crianças |
| [`HW.csv.gz`](dados/relevantes/HW.csv.gz) | **HW** | Antropometria e dosagem de hemoglobina/anemia materna e infantil | 28 países | **150.700** medições |
| [`CR.csv.gz`](dados/relevantes/CR.csv.gz) | **CR** | Casais pareados: entrevistas conjuntas entre cônjuges | 36 países | **109.174** casais |
| [`MR.csv.gz`](dados/relevantes/MR.csv.gz) | **MR** | Homens/parceiros entrevistados em idade reprodutiva | 36 países | **236.070** parceiros |
| [`SQ.csv.gz`](dados/relevantes/SQ.csv.gz) | **SQ** | Infraestrutura comunitária e serviços de saúde locais | 19 países | **5.154** registros |
| [`WI.csv.gz`](dados/relevantes/WI.csv.gz) | **WI** | Índice de riqueza (*wealth index*) adicional do DHS | 26 países | **190.832** registros |

> O arquivo [`dados/relevantes/manifesto_selecao.csv`](dados/relevantes/manifesto_selecao.csv) contém o registro de governança completo, detalhando o arquivo de origem, a fase DHS, a contagem de linhas e cada uma das colunas selecionadas em cada país.

---

## Otimização de Consultas (+20% de Pontuação)

1. Executar `EXPLAIN QUERY PLAN <consulta>` identificando operações de varredura completa (`SCAN TABLE`).
2. Criar índices adequados nas colunas de filtro ou chave estrangeira:
   ```sql
   CREATE INDEX idx_mulher_idade ON Mulher(v012);
   CREATE INDEX idx_nascimento_mulher ON Nascimento(id_mulher_global);
   ```
3. Executar novamente o plano de execução comprovando o uso do índice (`SEARCH TABLE ... USING INDEX`).
4. Medir e comparar o tempo de execução no Jupyter Notebook utilizando a diretiva `%timeit`.

---

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
