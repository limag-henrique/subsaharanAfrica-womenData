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
- Pesos dentro de cada país; ajustes descritivos com suporte comum, sem inferência causal ou populacional continental.
- Processamento, documentação, SQL, gráficos e benchmark executados no notebook.

## Testes confirmados

Execução completa do notebook; carga com PK/FK e M:N; resultados das dez consultas; equivalência antes/depois dos índices. Fixture independente cobre países distintos, identificadores formatados diferentemente e ausência de recodes complementares. SQL é a interface pública do artefato.

## Fora de escopo

Inferir matrículas, contribuições pessoais, impactos causais, modelos preditivos ou representatividade continental. Os módulos opcionais continuam disponíveis no banco de preparação, mas não são combinados entre fases incompatíveis.

## Notas

Escopo e pontos de teste confirmados pelo usuário nesta conversa. A especificação é local; não foi solicitado publicar uma issue nem informado um fluxo de triagem do projeto.
