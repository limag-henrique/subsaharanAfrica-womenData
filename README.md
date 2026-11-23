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

### Executar o notebook

```bash
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 "Saúde da Mulher na África Subsaariana.ipynb"
```

O comando executa todas as células em ordem e salva os resultados no próprio notebook.

O relatório usa `saude_mulher_final.db`, gerado localmente a partir da preparação.
Ano e mês são calculados nas views `Entrevista_Analitica` e `Nascimento_Analitico`;
as tabelas guardam apenas a data CMC. As bases de preparação são preservadas.
Os identificadores textuais mantêm os códigos de pesquisa, domicílio e pessoa;
`linha` só identifica uma pessoa em conjunto com seu domicílio.

Para reconstruir desde os CSVs e suplementos Stata autorizados, em um destino novo:

```bash
python scripts/reconstruir_relatorio.py --destino output/reconstrucao/saude_mulher_final.db --extraidos dados/completo/extraidos
```

O comando lê `docs/manifesto_contracepcao.json`; a pasta `--extraidos` deve conter
os arquivos Stata dos suplementos, sem duplicatas. O ER fornecido pelos autores
está em `docs/Diagrama_ER.jpg` e incorporado ao notebook.

### Como descompactar

Execute `python scripts/restaurar_arquivos.py` na raiz do projeto, no Windows, Linux ou macOS (use `python3` se necessário).

Reserve pelo menos **6 GiB livres** para restauração, preparação e banco final.

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

## Validação e exportação

```bash
python scripts/validar_relatorio.py
python scripts/gerar_diagramas.py
npm install --prefix tmp/diagramas --no-audit --no-fund mermaid
python scripts/renderizar_diagramas.py
python scripts/exportar_relatorio.py
```

O relacional usa o próprio Mermaid; o ER original é preservado pelos scripts.

A exportação usa Microsoft Edge ou Chromium (`python -m playwright install chromium`). O PDF e o HTML ficam em `output/pdf/`. Tabelas longas exibem uma amostra identificada no PDF; os resultados integrais permanecem no notebook. Os diagramas recebem páginas A3 para preservar a leitura.

A consulta 8 compara versões original e otimizada, verifica resultados idênticos e mede três execuções alternadas. O ganho depende do ambiente.

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
