# Dados compactos do projeto (Saúde da Mulher na África Subsaariana)

Esta pasta contém os microdados essenciais para o estudo da Saúde da Mulher nos 37 países comparáveis da África Subsaariana, consolidados em formato CSV compactado (gzip).

### Recodes Relevantes Mantidos:
- **`IR.csv.gz` (Individual Recode - Mulher):** 407.600 observações de mulheres em idade fértil (15–49 anos), contendo dados reprodutivos, uso e conhecimento contraceptivo, idade e escolaridade.
- **`BR.csv.gz` (Birth Recode - Nascimentos):** 877.412 registros de nascidos vivos, assistência ao pré-natal e ao parto.
- **`HR.csv.gz` (Household Recode - Domicílios):** 385.457 domicílios com informações de residência (urbana/rural), eletricidade, fonte de água e quintis de riqueza.
- **`PR.csv.gz` (Household Member Recode - Moradores):** 1.884.683 moradores que compõem os agregados familiares.
- **`KR.csv.gz` (Children's Recode - Crianças):** 282.641 crianças menores de 5 anos com dados de acompanhamento de saúde materna, diarreia e vacinação (`h2`–`h9`).
- **`MR.csv.gz` (Men's Recode - Parceiros):** 236.070 homens entrevistados nos domicílios pesquisados, utilizados como contexto intradomiciliar e de gênero conforme o Diagrama ER aprovado.

> **Nota:** Inquéritos fora do escopo relacional aprovado (como casais `CR`, antropometria legada `HW`, postos de saúde `SQ` e índices avulsos `WI`) foram descartados. A base normalizada (`saude_mulher_normalizado.db`) incorpora adicionalmente 10 pesquisas suplementares de contracepção (`176.404` entrevistas femininas independentes documentadas em `docs/manifesto_contracepcao.json`), totalizando **584.004** mulheres entrevistadas.
