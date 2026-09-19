# Projeto: Análise de Dados de Saúde na África Subsaariana (DCC011)

Este repositório contém a infraestrutura em Python para coleta, catalogação, organização e carga dos microdados de saúde do **The DHS Program (Demographic and Health Surveys)** referentes a **38 países da África Subsaariana**.

O projeto foi estruturado em conformidade com as diretrizes do **Trabalho Prático da disciplina DCC011 - Introdução a Banco de Dados** (`descrição.txt`), com ênfase especial nos questionários **IR (Individual Recode - Saúde da Mulher)** para obtenção da pontuação extra.

---

## 📁 Estrutura do Repositório

```text
África Subsaariana/
├── descrição.txt              # Especificação oficial do trabalho prático (DCC011)
├── urls_dhs.txt               # Lista consolidada dos 1.419 links de download do DHS
├── catalogo.py                # Módulo de metadados, classificação e geração de catálogo
├── catalogo_datasets.json     # Catálogo de todos os 1.419 datasets em JSON
├── catalogo_datasets.csv      # Catálogo de todos os 1.419 datasets em CSV
├── baixar_datasets.py         # Script principal de download, autenticação e organização
├── carregar_sqlite.py         # Utilitário para carregar dados .dta (Stata) no SQLite
├── .env.example               # Exemplo de configuração de credenciais de acesso
├── requirements.txt           # Dependências Python
└── dados/                     # Diretório de armazenamento (gerado automaticamente)
    ├── brutos/                # Arquivos .zip originais organizados por País e Categoria
    │   ├── Angola/
    │   │   ├── Saude_da_Mulher_IR/
    │   │   ├── Nascimentos_BR/
    │   │   └── Domicilios_HR/
    │   ├── Mocambique/
    │   └── ...
    └── extraidos/             # Arquivos .dta (Stata) descompactados para análise
```

---

## 🔐 Autenticação no DHS Program

Os microdados do **The DHS Program** são gratuitos para fins acadêmicos e de pesquisa, mas exigem uma conta cadastrada com um projeto aprovado no site oficial ([https://dhsprogram.com](https://dhsprogram.com)).

O script `baixar_datasets.py` suporta três formas de autenticação:

### Opção 1: Variáveis de Ambiente ou arquivo `.env` (Recomendado)
Crie um arquivo `.env` na raiz do projeto (ou configure suas variáveis de sistema):
```env
DHS_USER=seu_email@dominio.com
DHS_PASSWORD=sua_senha_aqui
```

### Opção 2: Linha de comando com argumentos CLI
```bash
python baixar_datasets.py --username "seu_email@dominio.com" --password "sua_senha"
```

### Opção 3: Sessão aberta no Navegador (Cookies)
Se você já está logado no site do DHS no seu navegador, você pode copiar os cookies da sessão (`CFID=...; CFTOKEN=...; JSESSIONID=...`) e passar pelo parâmetro:
```bash
python baixar_datasets.py --cookie "CFID=XXXXXX; CFTOKEN=YYYYYY; JSESSIONID=ZZZZZZ"
```

---

## 🚀 Como Executar o Download e a Organização

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Baixar apenas dados de Saúde da Mulher (Recode IR - Ponto Extra no Trabalho)
O DHS possui **205 datasets** específicos de mulheres em idade reprodutiva (15-49 anos), contendo dados sobre saúde reprodutiva, maternidade, pré-natal, exames e vacinação:
```bash
python baixar_datasets.py --women-health-only
```

### 3. Baixar dados de países específicos (Ex: Angola e Moçambique)
```bash
python baixar_datasets.py --country AO,MZ --recode IR,BR,HR
```

### 4. Baixar com descompactação automática dos arquivos Stata (`.dta`)
```bash
python baixar_datasets.py --country AO --extract
```

### 5. Baixar todos os 1.419 datasets
```bash
python baixar_datasets.py --workers 4
```

---

## 📊 Metadados dos Datasets

O código do arquivo no padrão DHS identifica o tipo de dados:
- **`IR`**: *Individual Recode* (Mulheres 15-49 anos - **Foco Saúde da Mulher**)
- **`BR`**: *Births Recode* (Histórico completo de nascimentos e partos)
- **`KR`**: *Children's Recode* (Crianças menores de 5 anos)
- **`HR`**: *Household Recode* (Características do domicílio e saneamento)
- **`PR`**: *Household Member Recode* (Listagem de moradores)
- **`CR`**: *Couples Recode* (Casais)
- **`MR`**: *Men's Recode* (Homens)
- **`HW`**: *Height and Weight* (Medições antropométricas e nutricionais)
- **`WI`**: *Wealth Index* (Indicador socioeconômico de riqueza)

---

## 🗄️ Integração com SQLite e Jupyter Notebook

Conforme estipulado na `descrição.txt` do trabalho prático:
> *"O SGBD SQLite embarcado em um Jupyter notebook deverá ser utilizado para implementação do banco de dados e execução das consultas."*

Após baixar e descompactar os arquivos com o argumento `--extract`, utilize o script `carregar_sqlite.py` para criar o banco de dados e as tabelas:

```bash
python carregar_sqlite.py "dados/extraidos/Angola/Saude_da_Mulher_IR/AOIR81DT/AOIR81FL.DTA" --db saude_africa.db --table mulheres_angola
```
