# Especificação do relatório DHS

## Problema

O relatório anterior conserva microdados redundantes, não implementa o M:N, não mede ganho de desempenho e concentra exemplos em Angola. O trabalho exige uma construção bottom-up e análises conjuntas dos países.

## Solução

Construir pelo notebook um banco normalizado separado, a partir do banco de preparação dos arquivos Stata. Preservar o núcleo IR/HR/PR/BR/KR, implementar conhecimento Mulher–Método e estudar diferenças entre países com estratificação socioeconômica.

## Histórias de uso

1. Como integrante, quero reproduzir obtenção e carga sem expor credenciais.
2. Como avaliador, quero rastrear a passagem dos microdados para as dependências funcionais e o esquema normalizado.
3. Como integrante, quero preservar todos os registros do núcleo sem inventar observações ausentes.
4. Como avaliador, quero PK, FK, restrições e um relacionamento M:N efetivamente carregado.
5. Como leitor, quero diagramas anexados que correspondam ao banco executado.
6. Como avaliador, quero dez consultas nas quatro categorias exigidas, acompanhadas de resultados e interpretação.
7. Como leitor, quero comparações dos 37 países, distinguindo cobertura e composição da amostra.
8. Como analista, quero confrontar diferenças brutas e ajustadas por riqueza e escolaridade.
9. Como avaliador, quero planos e tempos antes/depois dos índices, com resultados equivalentes.
10. Como integrante, quero manter contribuições individuais pendentes até confirmação humana.

## Decisões de implementação

- Banco derivado separado, origem em modo somente leitura, sem alterar branch ou criar commits.
- Chaves naturais numéricas, evitando as diferenças de espaços em caseid.
- Identificar domicílios sem HR e nascimentos suplementares de KR; não transformá-los em novos entrevistados.
- Nove métodos de conhecimento com semântica estável; não reinterpretar v307 entre fases.
- Anos de dois dígitos reconstruídos por CMC, com testes; as pesquisas de 1989–1990 e 1994–1995 não são apresentadas como recentes.
- Pesos dentro de cada país; ajustes descritivos com suporte comum, sem inferência causal ou populacional continental.
- Processamento, documentação, SQL, gráficos e benchmark executados no notebook.
- Acrescentar dez IR completos locais (176.404 entrevistas), com seleção explícita em manifesto e coortes independentes. A seleção anterior perde fases alfanuméricas e escolhe arquivos sem módulo contraceptivo; não usar suas respostas ausentes como não uso.
- Comparação contraceptiva em todos os 37 países, com uma pesquisa por país e período explícito; padronização possível em 35, pois Sudão/República Centro-Africana carecem de contexto socioeconômico necessário. Nunca unir mulheres entre pesquisas.

## Testes confirmados

Execução completa do notebook; carga com PK/FK e M:N; resultados das dez consultas; equivalência antes/depois dos índices. Fixture independente cobre países distintos, identificadores formatados diferentemente e ausência de recodes complementares. SQL é a interface pública do artefato.

## Fora de escopo

Inferir matrículas, contribuições pessoais, impactos causais, modelos preditivos ou representatividade continental. Os módulos opcionais continuam disponíveis no banco de preparação, mas não são combinados entre fases incompatíveis.

## Notas

## Apresentação visual — alinhamento de 11/10/2026

O leitor deve conseguir avaliar as sete seções sem percorrer tabelas extensas ou a implementação da carga. Organização confirmada: dez comandos SQL visíveis, gráficos por consulta e tabelas completas sob demanda; código de preparação recolhido. A normalização, origem Stata, M:N, tema de saúde da mulher e benchmark de otimização permanecem verificáveis. Contribuições individuais e matrículas desconhecidas continuam pendentes.

Preservar as consultas, coortes e fórmulas existentes. Validar pela execução completa do notebook, testes de integração já existentes e inspeção visual dos gráficos e diagramas. A execução de revisão usa um banco derivado temporário para preservar o banco local previamente alterado. Não publicar issue, mudar branch ou criar commits.

Escopo e pontos de teste confirmados pelo usuário nesta conversa. A especificação é local; não foi solicitado publicar uma issue nem informado um fluxo de triagem do projeto.

## Carga visível no notebook — 13/10/2026

O notebook Saúde da Mulher na África Subsaariana mostra o DDL das dez tabelas e uma função de carga idempotente. Os CSVs IR/HR/PR/BR/KR são lidos em lotes, com seleção explícita de colunas; MR e CR não são lidos. O esquema por país é necessário porque os CSVs consolidados têm larguras variáveis. Como o manifesto original foi retirado, docs/esquemas_csv.csv conserva os 171 esquemas dos recodes centrais recuperados da versão de preparação bcfad39. Cabeçalhos, contagens e metadados são conferidos na leitura.

Um banco populado é aberto somente para leitura e reutilizado após verificar o esquema e PRAGMA foreign_key_check. Banco ausente ou vazio dispara a carga em arquivo temporário; a normalização conserva chaves, ausências e origem dos registros antes de substituir o destino. Vínculos inválidos interrompem a execução. Os CSVs reproduzem as 407.600 entrevistas do núcleo; suplementos são opcionais e independentes, e o banco existente conserva os que já foram carregados.

Verificação na interface pública SQL: carga com CSVs de larguras distintas, exclusão de MR, contexto familiar, conversão de peso/ano, M:N, banco vazio, reutilização sem alteração e bloqueio de FK inválida. A validação real usa um banco derivado temporário, sem alterar os bancos existentes.
