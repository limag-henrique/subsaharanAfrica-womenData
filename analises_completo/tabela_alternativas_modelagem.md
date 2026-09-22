# Alternativas de modelagem: saúde da mulher na África Subsaariana

## Critério adotado

Os arquivos `.DTA` do DHS são recodes de levantamentos diferentes, e não tabelas que possam ser juntadas apenas pelo nome do país. Para tornar a comparação entre países defensável, esta tabela usa duas referências:

- **Inventário completo:** todos os arquivos locais, 1.409 `.DTA`, 37 países comparáveis mais o grupo `África do Sul (Histórico/Outro)`, em todas as ondas. As linhas incluem repetições de país e de pessoas em ondas diferentes.
- **Base comparável:** uma onda mais recente disponível por grupo, escolhida pela maior fase no nome do arquivo. O resultado tem 38 grupos e 411.813 mulheres; excluindo o grupo histórico, são **37 países e 407.600 mulheres**. Essa é a base recomendada para a primeira análise conjunta.

Uma instância significa uma ocorrência que será transformada em registro da entidade ou do relacionamento. Portanto, o número de linhas de um recode é uma contagem de registros de origem, não necessariamente o número de pessoas únicas em todas as ondas.

## Contagem bruta por recode

| Recode | Conceito principal | Arquivos locais | Países/grupos | Linhas em todas as ondas | Linhas na base comparável | Entidade(s) sugerida(s) |
|---|---|---:|---:|---:|---:|---|
| IR | Mulheres entrevistadas, 15–49 anos | 203 | 38 | 2.135.364 | 411.813 (407.600 sem histórico) | `Mulher` |
| BR | Nascimentos e histórico obstétrico | 167 | 38 | 5.211.100 | 883.503 (877.412 sem histórico) | `Nascimento` / `Gestacao_Parto` |
| HR | Domicílio, saneamento e bens | 194 | 36 | 1.927.659 | 385.457 | `Domicilio` |
| PR | Moradores do domicílio | 195 | 36 | 9.921.593 | 1.884.683 | `Morador` |
| KR | Crianças menores de cinco anos | 200 | 38 | 1.558.488 | 285.923 (282.641 sem histórico) | `Crianca` |
| CR | Casais | 141 | 36 | 343.728 | 67.669 (67.006 sem histórico) | `Casal` |
| MR | Homens relacionados ao casal | 142 | 36 | 729.685 | 148.332 (144.714 sem histórico) | `Homem` / `Parceiro` |
| HW | Antropometria e anemia | 67 | 29 | 341.755 | 4.445 (2.816 sem histórico) | `Medicao_Saude` |
| SQ | Serviços e infraestrutura de saúde | 25 | 19 | 6.548 | não há arquivo na mesma fase para a seleção automática | `Servico_Saude` |
| WI | Riqueza e contexto socioeconômico | 39 | 26 | 265.967 | 5.551 | atributos de `Domicilio` ou `Indice_Riqueza` |
| DV | Violência doméstica | 1 | 1 | 2.983 | 2.983 | `Violencia_Autonomia` |

Os números da coluna “base comparável” são contagens de registros dos arquivos da onda escolhida. Quando um recode não existe naquela onda, ele não deve ser preenchido artificialmente por outra onda; deve ser tratado como cobertura ausente.

## Alternativas de escopo para o modelo ER

As alternativas abaixo são cumulativas. Em todas elas, `Pais` tem 37 instâncias na base recomendada e `Levantamento` tem 37 instâncias, uma por país. O grupo histórico pode ser incluído como uma 38ª unidade analítica, mas deve permanecer identificado como histórico.

| Alternativa | Recodes | Entidades e instâncias na base recomendada | Relacionamentos e instâncias esperadas | Avaliação |
|---|---|---|---|---|
| **Recomendado por Henrique** | IR, BR, HR, PR, KR; HW, CR/MR, SQ e WI como módulos opcionais | `Pais`, `Levantamento`, `Mulher`, `Domicilio`, `Nascimento`, `Crianca`, `Metodo_Contraceptivo`; módulos opcionais `Medicao_Saude`, `Casal`, `Parceiro`, `Servico_Saude`, `Indice_Riqueza` | `Pertence_A` (`Domicilio–Pais`); `Reside_Em` (`Mulher–Domicilio`); `Tem_Nascimento` (`Mulher–Nascimento`); `Tem_Crianca` (`Mulher–Crianca`); `Usa_ou_Conhece` (`Mulher–Metodo`, N:M, contando fatos derivados de `v301–v307/v312`); `Participa_de` (`Mulher–Levantamento`) | **Recomendação final:** atende aos requisitos de entidades, relacionamentos e futura análise entre países sem fingir cobertura onde o recode não existe. |

## Instâncias dos relacionamentos do modelo recomendado

| Relacionamento | Cardinalidade | Instâncias na base de 37 países | Chave ou regra de construção |
|---|---:|---:|---|
| `Pertence_A(Domicilio, Pais)` | N:1 | 385.457 registros HR disponíveis | `pais_id` + `id_domicilio`; se o domicílio for derivado de IR, preservar a onda. |
| `Reside_Em(Mulher, Domicilio)` | N:1 | 407.600, uma por mulher | `pais_id` + `levantamento_id` + `v001` + `v002`; o vínculo pode existir mesmo quando o HR correspondente não foi baixado. |
| `Participa_de(Mulher, Levantamento)` | N:1 | 407.600 | Uma mulher pertence a exatamente um arquivo/onda selecionado na base comparável. |
| `Tem_Nascimento(Mulher, Nascimento)` | 1:N | 877.412 registros BR | Usar `caseid` da mãe e o índice do nascimento; não confundir com número de partos recentes. |
| `Tem_Crianca(Mulher, Crianca)` | 1:N | 282.641 registros KR | Usar identificador da mãe/respondente e índice da criança. |
| `Tem_Morador(Domicilio, Morador)` | 1:N | 1.884.683 registros PR | Chave do domicílio + linha do morador. |
| `Relaciona_Casal(Mulher, Casal)` | 1:N ou 1:1, conforme o levantamento | 67.006 registros CR | Validar o identificador de pareamento no dicionário da onda. |
| `Possui_Medicao(Mulher, Medicao_Saude)` | 1:N | 2.816 registros HW nos 37 países | Só inserir quando `HW` tiver a mesma onda e chave compatível. |
| `Usa_ou_Conhece(Mulher, Metodo_Contraceptivo)` | N:M | **a calcular na carga** | Contar uma linha por par mulher–método a partir das variáveis de conhecimento/uso; `v312` sozinho representa apenas o método atual. |

## Decisões importantes para a integração futura

1. Criar `Levantamento` como entidade, mesmo que ela não estivesse no primeiro rascunho. Sem ela, uma mesma mulher, domicílio ou país de ondas diferentes pode ser confundida com uma instância única.
2. Formar identificadores com país, onda e identificador original. Exemplos: `id_mulher = pais + levantamento + caseid`; `id_domicilio = pais + levantamento + v001 + v002`; `id_nascimento = id_mulher + índice_do_nascimento`.
3. Não somar as linhas de todas as ondas para produzir uma prevalência continental. A soma de 2.135.364 linhas IR é um inventário de registros, não uma população de 2.135.364 mulheres únicas.
4. O relacionamento N:M recomendado é `Mulher–Metodo_Contraceptivo`, materializado por uma tabela associativa com atributos como `conhece`, `já_usou`, `usa_atualmente` e `tipo_de_metodo`. A contagem final desse relacionamento só deve ser publicada depois da extração dessas variáveis.
5. A análise de violência/autonomia pode ser adicionada como módulo opcional. A auditoria encontrou rótulos relacionados em 35 de 38 grupos, mas ausência de rótulo não significa ausência do fenômeno.

## Recomendação

Para o relatório parcial, escolher a alternativa **H**, implementando primeiro o núcleo `Pais–Levantamento–Mulher–Domicilio–Nascimento–Metodo_Contraceptivo` e deixando `Crianca`, `Medicao_Saude`, `Casal`, `Parceiro`, `Servico_Saude`, `Indice_Riqueza` e `Violencia_Autonomia` como extensões condicionadas à cobertura. Ela fornece pelo menos quatro entidades, pelo menos três relacionamentos e um relacionamento N:M, mantendo a futura comparação conjunta entre os 37 países interpretável.
