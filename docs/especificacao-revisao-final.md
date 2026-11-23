# Revisão final do notebook

## Escopo e critérios de aceitação

- Preservar as dez consultas na distribuição 2/3/3/2 e o bônus por tema e otimização.
- Incorporar o JPG fornecido pelo autor, sem redesenhá-lo.
- Manter a identidade textual composta de pesquisa, domicílio e pessoa; explicar a chave alternativa `(domicilio_id, linha)` e o vínculo de entrevista por PK/FK.
- Eliminar a redundância persistida ano/mês/CMC em entrevistas e partos, expondo as datas derivadas em views. Produzir um banco final separado e não alterar as bases de preparação.
- Corrigir a interpretação de conhecimento dos métodos selecionados e seu denominador; não interpretar códigos locais de assistência sem validação.
- Comparar sazonalidade e contracepção na mesma pesquisa e explicitar períodos, cobertura e sensibilidade às exclusões.
- Tornar a reconstrução desde os CSVs/suplementos executável sem montagem manual de argumentos.
- Executar o notebook completo, conferir equivalência da otimização, integridade referencial, diagramas e exportação PDF.

## Validação

As interfaces observáveis são o banco publicado pela preparação e os comandos SQL efetivos do notebook. Usar fixtures com resultados conhecidos para datas, identidade e denominadores, além da execução integral sobre a base real. Reutilizar os testes existentes de consultas e correspondência DDL–diagrama.

## Fora do escopo

Alterar a composição do grupo, inventar contribuições individuais, afirmar indicadores epidemiológicos oficiais, publicar externamente ou criar commits. A nota final depende da avaliação docente e da apresentação.

## Decisões aplicadas

- O indicador de conhecimento usa seis métodos fixos (pílula, DIU, injetáveis, preservativo masculino, esterilizações feminina e masculina). O item diafragma/espuma/gel permanece no catálogo e na auditoria, mas foi excluído do indicador composto pelo padrão de códigos 7 em 25 levantamentos. Ausências não viram respostas negativas.
- A consulta 9 descreve pré-natal e cesárea nos últimos 60 meses; não classifica local de parto sem os dicionários específicos.
- O ER entregue é o JPG dos autores, incorporado sem alteração; o relacional é gerado do DDL final. Ano/mês do ER são atributos derivados em views.

## Validação concluída em 23/11/2026

- `python scripts/test_normalizacao_final.py`: dois testes passaram (datas, identidade, índices derivados e migração com o DDL reduzido).
- `python scripts/validar_relatorio.py`: quatro testes passaram (denominadores, conhecimento e correspondência do diagrama com o DDL).
- Notebook integral: 20 células executadas, dez consultas com resultados, nenhuma saída de erro; integridade e FKs verificadas no próprio relatório.
- Migração integral adicional desde `saude_mulher_normalizado.db` e `saude_mulher_dhs.db`: concluída; o arquivo temporário de conferência foi removido após a validação.
- Otimização: 20 grupos idênticos; medianas registradas de 2,388 s e 1,964 s (razão 1,22). Tempos dependem do ambiente.
- Exportação: PDF com 31 páginas; conferidas visualmente as páginas dos diagramas, pré-natal/cesárea, consulta 10 e auditoria. Nenhuma página vazia detectada.
- JPG incorporado: hash igual ao arquivo fornecido. `git diff --check` passou; Graphify atualizado localmente.

Não foi refeita a extração integral desde os Stata, que não estão presentes neste checkout. O comando correspondente foi disponibilizado e o caminho de migração das bases restauráveis foi validado com dados reais.
