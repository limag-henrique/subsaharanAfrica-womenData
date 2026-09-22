# Auditoria de entidades e denominações dos dados DHS

## Escopo e método

- Foram encontrados **38 países**, **1409 arquivos `.DTA`** e **29.15 GiB** de microdados locais.
- A análise foi feita pelos metadados Stata (nomes de variáveis e rótulos), sem carregar as observações completas.
- O catálogo contém **1419 pacotes**, dos quais **205 IR**; a pasta analisada contém os recodes listados abaixo.
- Os recodes encontrados na pasta analisada são: **AT=1, BR=167, CR=141, DV=1, HA=1, HB=1, HH=15, HR=194, HW=67, IA=1, IQ=6, IR=203, KR=200, ML=4, MR=142, OL=1, PR=195, SQ=25, VA=5, WI=39**.
- Foram encontradas **1400 correspondências** entre os stems locais e o catálogo; a diferença de nomes ocorre porque o pacote usa sufixo `DT` e o arquivo extraído usa `FL`.
- Pacotes do catálogo sem `.DTA` local: **GHHH51FL, GHOD51FL, GHVA7IFL, MZOD51FL, SNBR71FL, SNBR7IFL, SNCR71FL, SNCR7IFL, SNHR71FL, SNHR7IFL, SNIR71FL, SNIR7IFL, SNKR71FL, SNKR7IFL, SNMR71FL, SNMR7IFL, SNPR71FL, SNPR7IFL, ZAOD71FL**.

## Resultado principal

Cada país possui entre **1,832** e **39,503** variáveis distintas no conjunto de seus arquivos Stata extraídos.
Há **559 nomes de variáveis exatamente iguais** presentes em todos os 38 países. A lista completa está no arquivo `variaveis_comuns_37_paises.csv`.

As denominações compartilhadas não devem ser comparadas apenas pelo texto bruto: o DHS mantém códigos estáveis (por exemplo, `v012`, `v106`, `v201`, `v312`) enquanto os rótulos mudam com abreviações, idioma do questionário, `NA` e versões do levantamento. A lista completa normalizada está em `denominacoes_normalizadas.csv`; a interseção universal está em `denominacoes_comuns_todos_paises.csv`.

### Núcleo comum de entidades/conceitos

- Identificação e amostragem: `caseid`, país/fase, cluster, domicílio, linha da respondente, peso amostral e datas da entrevista.
- Demografia: idade, grupos etários, nascimento, região e situação urbana/rural.
- Educação e contexto: nível/anos de escolaridade, alfabetização, água, banheiro e material do domicílio.
- História reprodutiva: filhos nascidos, filhos vivos, gravidez atual, nascimentos recentes e histórico de nascimentos (`b0`–`b12`).
- Saúde reprodutiva: gravidez, contracepção e intenção/desejo de filhos.
- Entrevista: completude, duração, visitas e identificação da entrevistadora.

## Entidades canônicas para o modelo relacional

Os `.DTA` são arquivos de microdados, não um esquema relacional pronto; por isso, “entidade” aqui significa um conceito que pode ser normalizado em tabela:

- `Pais`: código/onda e região do país; funciona como dimensão de comparação.
- `Mulher`: `caseid` e atributos demográficos, educacionais, reprodutivos e de saúde da entrevistada; nasce principalmente de `IR`.
- `Domicilio`: cluster, domicílio, residência, riqueza, água, banheiro e bens; combina `IR`, `HR` e `PR` quando necessário.
- `Gestacao_Parto_Nascimento`: gravidez, pré-natal, local/assistência do parto e histórico de nascimentos; combina `IR` e `BR`.
- `Metodo_Contraceptivo`: catálogo/dimensões de método e uso atual; atributos centrais em `IR`.
- `Violencia_Autonomia`: bloco opcional das variáveis `d*`/módulo de violência e decisões/permissão; não deve ser criado como entidade presente em todos os países.
- `Crianca` e `Servico_Saude`: entidades opcionais vindas de `KR`/`HW` e `SQ`, conforme a pergunta analítica.

## Equivalência semântica

Foi aplicada normalização de caixa, acentos, pontuação, espaços e marcadores `NA`. Para não misturar fenômenos distintos, as equivalências foram agrupadas por família temática; os resultados estão em [familias_semanticas.csv](familias_semanticas.csv).

- Violência física: `physical violence`, `physically hurt`, `slapped`, `punched`, `kicked`, `pushed`, ferimentos e hematomas.
- Violência emocional: `emotional violence/abuse`, humilhação, ameaça, insulto e fazer a mulher se sentir mal.
- Violência sexual: `sexual violence`, `forced sexual act/sex` e estupro/violação quando o rótulo aparece.
- Autonomia e controle: decisão sobre contracepção e permissão para buscar atendimento médico. Esses rótulos são relacionados à autonomia de gênero, mas não devem ser contabilizados automaticamente como agressão física ou abuso.

O módulo de violência/autonomia aparece em **35 dos 38 países**; os grupos sem rótulos correspondentes são **República Centro-Africana, Sudão, África do Sul (Histórico/Outro)**. Isso é cobertura de questionário, não uma conclusão de que não existe violência nesses países.

## A separação atual está correta?

A seleção `IR` está tecnicamente correta para mulheres entrevistadas de 15–49 anos e contém grande parte da saúde reprodutiva, materna, contracepção, HIV/IST e violência doméstica. Contudo, classificá-la como o conjunto completo de saúde da mulher é incompleto: parto/nascimento, domicílio, antropometria, crianças, serviços e módulos especiais estão distribuídos em outros recodes.

A categorização recomendada é manter `IR` como tabela/fonte central da mulher e adicionar, conforme a pergunta analítica, `BR` (nascimentos), `HR`/`PR` (domicílio e moradores), `HW` (antropometria), `KR` (criança), e módulos `SQ`, `ML`, `VA`, `HH`, `IQ` ou `OD` somente quando existirem no país e forem necessários. A cobertura por país e recode está em [cobertura_recodes_catalogo.csv](cobertura_recodes_catalogo.csv).

A classificação operacional por recode e por arquivo está em [classificacao_recodes_saude_mulher.csv](classificacao_recodes_saude_mulher.csv) e [inventario_arquivos.csv](inventario_arquivos.csv). Módulos auxiliares fora do catálogo principal foram marcados como `modulo_nao_mapeado` ou `modulo_especial` e devem ser validados pelo dicionário antes de entrar no modelo relacional.

## Possibilidade de repetir o download

- O login DHS foi testado com as credenciais já configuradas em `.env` e foi aceito; um projeto aprovado foi selecionado.
- O fluxo foi corrigido para ler `catalogo_datasets.csv`, que contém as 1.419 URLs, em vez de depender do inexistente `urls_dhs.txt`.
- A repetição completa é operacionalmente possível com `--urls-file catalogo_datasets.csv`; ela deve ser feita para uma pasta separada, pois o catálogo é muito maior que o subconjunto IR local.
- O download completo pode consumir dezenas de gigabytes e tempo significativo. A análise atual não baixa novamente arquivos que já foram auditados; ela deixa o fluxo pronto para execução autenticada e preserva o conjunto local original.

## Artefatos

- [inventario_arquivos.csv](inventario_arquivos.csv): um registro por `.DTA` local.
- [presenca_variaveis_por_pais.csv](presenca_variaveis_por_pais.csv): presença, rótulos e temas por país/variável.
- [variaveis_comuns_37_paises.csv](variaveis_comuns_37_paises.csv): interseção exata dos nomes (o sufixo do nome preserva o artefato original).
- [variaveis_comuns_todos_paises.csv](variaveis_comuns_todos_paises.csv): cópia com nome independente do número de países.
- [denominacoes_normalizadas.csv](denominacoes_normalizadas.csv): rótulos após normalização.
- [denominacoes_comuns_todos_paises.csv](denominacoes_comuns_todos_paises.csv): somente as denominações presentes em todos os grupos.
- [cobertura_temas.csv](cobertura_temas.csv) e [familias_semanticas.csv](familias_semanticas.csv): cobertura temática e equivalência semântica.
- [cobertura_recodes_catalogo.csv](cobertura_recodes_catalogo.csv): recodes disponíveis no catálogo por país.
- [classificacao_recodes_saude_mulher.csv](classificacao_recodes_saude_mulher.csv): categorização operacional para o escopo mulher.