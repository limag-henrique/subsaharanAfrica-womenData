# Dados compactos do projeto

Esta pasta contém apenas uma onda recente por país comparável (exclui `OS`, África do Sul histórica), os recodes do modelo integrado e as variáveis necessárias às entidades e relacionamentos. Os cinco recodes centrais (IR/BR/HR/PR/KR) usam a mesma fase; os módulos opcionais usam a fase mais recente disponível e só devem ser unidos quando as chaves forem compatíveis. Os arquivos estão em CSV gzip.

Consulte `manifesto_selecao.csv` para a origem, fase, quantidade de linhas e colunas de cada arquivo. Os microdados brutos não devem ser versionados.

Resumo atual: `IR` 407.600 mulheres em 37 países; `BR` 877.412 nascimentos; `HR` 385.457 domicílios; `PR` 1.884.683 moradores; `KR` 282.641 crianças. Os módulos opcionais disponíveis são `HW` (28 países), `CR` (36), `MR` (36), `SQ` (19) e `WI` (26).
