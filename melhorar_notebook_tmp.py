import base64
import hashlib
import io
import json
import contextlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parent
nb=json.loads((ROOT/'tp_template.ipynb').read_text(encoding='utf-8'))
cells=[]
def md(s): cells.append({'cell_type':'markdown','metadata':{},'source':s.strip().splitlines(True)})
def code(s,tags=None): cells.append({'cell_type':'code','metadata':{'tags':tags or []},'source':s.strip().splitlines(True),'execution_count':None,'outputs':[]})
def diagram(rel=False):
    labels=[
      ('Pais','PK código\nnome'),('Levantamento','PK id\nFK país; fase'),
      ('Domicilio','PK id\nFK levantamento\ncluster; número; residência; riqueza'),
      ('Mulher','PK id\nFK domicílio\nlinha; idade; escolaridade; filhos'),
      ('Entrevista','PK/FK mulher\nano; mês; data CMC; peso; usa método'),
      ('Nascimento','PK id\nFK mulher\níndice; ano; sexo; pré-natal; origem'),
      ('Crianca','PK/FK nascimento\nidade; diarreia; cartão de vacina'),
      ('Morador','PK id\nFK domicílio\nlinha; sexo; idade; escolaridade'),
      ('Conhecimento_Metodo','PK/FK mulher + método\nnível de conhecimento'),
      ('Metodo','PK id\nnome; classe')]
    positions={name:(col*4.0,row*2.1) for (name,_),(col,row) in zip(labels,[(0,3),(1,3),(1,2),(1,1),(0,1),(2,1),(2,0),(2,2),(0,0),(0,2)])}
    fig,ax=plt.subplots(figsize=(14,10)); ax.set(xlim=(-.9,12),ylim=(-.2,8.2)); ax.axis('off')
    edges=[('Pais','Levantamento','1:N'),('Levantamento','Domicilio','1:N'),('Domicilio','Mulher','1:N'),('Domicilio','Morador','1:N'),('Mulher','Entrevista','1:1'),('Mulher','Nascimento','1:N'),('Nascimento','Crianca','1:0..1'),('Mulher','Conhecimento_Metodo','1:N'),('Metodo','Conhecimento_Metodo','1:N')]
    for a,b,l in edges:
        x,y=positions[a]; u,v=positions[b]
        if a=='Metodo' and b=='Conhecimento_Metodo':
            ax.plot([x,-.5,-.5,u],[y+.65,y+.65,v+.65,v+.65],color='#668398',lw=1.5,zorder=0)
            ax.text(-.5,(y+v)/2+.65,l if not rel else 'FK',fontsize=9,ha='center',va='center',bbox={'facecolor':'white','edgecolor':'none','pad':2},zorder=4)
            continue
        ax.annotate('',xy=(u+1.6,v+.65),xytext=(x+1.6,y+.65),arrowprops={'arrowstyle':'-','color':'#668398','lw':1.5},zorder=0)
        ax.text((x+u)/2+1.6,(y+v)/2+.65,l if not rel else 'FK',fontsize=9,ha='center',va='center',bbox={'facecolor':'white','edgecolor':'none','pad':2},zorder=4)
    for name,attrs in labels:
        x,y=positions[name]
        ax.add_patch(FancyBboxPatch((x,y),3.2,1.3,boxstyle='round,pad=.03',facecolor='#eef5fa',edgecolor='#2d5970',zorder=2))
        ax.text(x+1.6,y+.65,name+'\n'+(attrs if rel else attrs.replace('PK/FK','Identificador / vínculo').replace('PK','Identificador').replace('FK','Vínculo')),fontsize=8.3,ha='center',va='center',zorder=3)
    ax.set_title('Esquema relacional normalizado' if rel else 'Modelo ER implementado — Mulher–Método é M:N via Conhecimento',fontsize=15)
    fig.tight_layout(); out=io.BytesIO(); fig.savefig(out,format='png',dpi=150,bbox_inches='tight'); plt.close(fig)
    name='relacional.png' if rel else 'er.png'
    cells.append({'cell_type':'markdown','metadata':{},'source':[f'![Diagrama](attachment:{name})'],'attachments':{name:{'image/png':base64.b64encode(out.getvalue()).decode()}}})

md('# 1. Título\n\n**Saúde da Mulher na África Subsaariana**\n\nDesigualdades entre países, residência, riqueza e escolaridade — TZ1 / DCC011')
md('''# 2. Membros (nome e número de matrícula)

| Integrante | Matrícula |
|---|---|
| Henrique Lima Gusmão | 2025014508 |
| Felipe Pires Franco | A informar |
| Izabella Galdino Correia | A informar |
| Alice Lina Oliveira da Silva | A informar |''')
md('''# 3. Descrição, obtenção e processamento dos dados

O projeto utiliza microdados **DHS, originalmente distribuídos em Stata (.DTA)**, sobre saúde da mulher e condições de vida em **37 países da África Subsaariana**. O banco de preparação do repositório reúne **4.529.723 linhas em dez recodes**, incluindo **407.600 mulheres**, **877.412 nascidos vivos BR**, **385.457 domicílios HR**, **1.884.683 moradores PR** e **282.641 crianças KR**. Somar recodes não equivale a contar pessoas distintas.

O foco em saúde da mulher contempla o ponto extra temático. O núcleo normalizado deste trabalho é **IR/HR/PR/BR/KR**; os módulos complementares continuam no banco de preparação, pois sua fase pode diferir da pesquisa da mulher. Os 108 levantamentos do catálogo local não são 108 pesquisas de mulheres selecionadas: o IR contém uma pesquisa por país, em anos diferentes.

**Pergunta central:** quanto das diferenças de contracepção e pré-natal entre contextos rurais e urbanos se relaciona à composição de riqueza e escolaridade de cada país? Vamos comparar diferenças brutas e padronizadas, cobertura dos indicadores e heterogeneidade entre países. Não presumimos que um padrão continental descreve cada país nem que uma associação revela causalidade.

### 3.1 Como obter e reproduzir

1. Solicitar acesso aos países/levantamentos no [portal DHS](https://dhsprogram.com/data/Access-Instructions.cfm). Os microdados exigem autorização; o [catálogo de datasets da API](https://api.dhsprogram.com/rest/dhs/datasets) é público. Não registrar credenciais no notebook.
2. Instalar Git LFS antes de clonar o repositório indicado no README e instalar `requirements.txt`. Abrir o notebook em um editor compatível com Jupyter; as dependências de execução, gráficos e validação estão no arquivo de requisitos.
3. Usar o catálogo local e os scripts abaixo; a API/catalogação informa a origem, enquanto o manifesto registra arquivo, fase, variáveis e quantidade de linhas selecionadas.

```bash
python database_python/baixar_datasets.py --urls-file catalogo_datasets.csv --recode IR,BR,HR,PR,KR --extract --output-dir dados/completo
python database_python/preparar_dados_projeto.py --source dados/completo/extraidos --output dados/relevantes
python database_python/carregar_sqlite.py
```

Os argumentos/defaults do preparador devem corresponder ao caminho de extração adotado; seus defaults usam os dados completos locais. **Não usar `pd.read_csv` diretamente nos compactos consolidados**: a largura das linhas varia por país e o loader existente usa `manifesto_selecao.csv` para alinhá-las. O SQLite de origem é uma etapa de preparação dos arquivos Stata, não um dataset originalmente fornecido em SQL.

### 3.2 Construção bottom-up e normalização

Partimos dos recodes e dos dicionários; identificamos chaves e dependências funcionais; decompomos os atributos; carregamos as relações normalizadas; e mapeamos esse esquema para os diagramas ER/relacional das seções 4 e 5.

| Dependência identificada | Decomposição |
|---|---|
| Código do país → nome | Pais |
| Levantamento → país, fase | Levantamento |
| Levantamento + cluster + domicílio → contexto habitacional | Domicilio |
| Domicílio + linha da mulher → perfil individual | Mulher |
| Mulher → data, peso e resposta contraceptiva da entrevista selecionada | Entrevista |
| Mulher + índice do nascimento → histórico de cada nascido vivo | Nascimento |
| Nascimento → acompanhamento infantil KR, quando disponível | Crianca |
| Domicílio + linha do morador → perfil do morador | Morador |
| Método → nome, classificação | Metodo |
| Mulher + método → nível de conhecimento | Conhecimento_Metodo |

**1FN:** atributos escalares e identificadores únicos; as nove colunas repetidas de conhecimento são transformadas em linhas Mulher–Método. **2FN:** o nível depende do par completo mulher–método, não apenas de um deles. **3FN:** nome do país, fase, contexto habitacional e nome/classificação do método ficam em suas próprias relações. As entidades filhas não repetem país/levantamento; esses dados são obtidos pelas FKs. Identificadores técnicos concatenados codificam as chaves naturais, e restrições `UNIQUE` as explicitam.

**Cuidados de integração:** `caseid` tem espaços incompatíveis em alguns recodes. Usamos `(levantamento, cluster, domicílio, linha)` para identificar a mulher, e acrescentamos `bidx` para o nascimento. Os 5.189 domicílios do Sudão sem HR conservam o contexto observado em IR, com condições habitacionais ausentes e origem `IR_sem_HR`. Os 53.333 registros KR sem BR geram nascimentos `KR_sem_BR`, sem duplicar aqueles já presentes em BR. Nenhuma mãe é inventada.

### 3.3 Semântica e indicadores

- `v212` é idade no primeiro **nascimento**, não na primeira gestação; BR representa nascidos vivos.
- `v304` é conhecimento do método; `v305` e `v307` não devem ser intercambiados. `v307` muda de significado entre fases. Para o M:N usamos os nove métodos iniciais, de significado estável, preservando nível 0–7; nível positivo indica conhecimento. Ausência e códigos especiais não viram “não conhece”. Isso é um recorte explícito, não o catálogo completo de métodos.
- `v312=0` indica nenhum método atual; códigos válidos 1–19 indicam algum método. Não classificamos todos como modernos nem inferimos autonomia pelo uso.
- `m14` é o código da quantidade de consultas. Para a análise, 0–90 são valores numéricos válidos; NULL/98/99 não são zero. O limiar de quatro consultas é uma comparação descritiva histórica, não a definição atual de cuidado adequado.
- `m3a/m3b` descrevem assistência ao parto, e a categoria m3b varia por país. Esses campos ficam preservados, mas não são usados como indicador continental completo de assistência qualificada.
- Pesos são `v005/1.000.000`. Calculamos proporções dentro de cada país/levantamento; somar esses pesos entre países não estima a população da África Subsaariana. Não calculamos intervalos de confiança sem desenho amostral completo.

Fontes para os códigos: [rotina oficial DHS de conhecimento contraceptivo](https://github.com/DHSProgram/DHS-Indicators-Stata/blob/master/Chap07_FP/FP_KNOW.do), [manual de recodificação DHS7](https://dhsprogram.com/pubs/pdf/DHSG4/Recode7_DHS_10Sep2018_DHSG4.pdf) e [manual de amostragem DHS](https://dhsprogram.com/pubs/pdf/DHSM4/DHS6_Sampling_Manual_Sept2012_DHSM4.pdf).

### 3.4 Processamento executável

Execute as células na ordem, na raiz do repositório. A carga constrói **saude_mulher_normalizado.db** por meio de um arquivo temporário, valida a integridade e só então substitui o resultado derivado anterior. A origem é anexada em modo somente leitura. As restrições de FK permanecem ligadas durante a carga.''')
code((ROOT/'pipeline_notebook_tmp.py').read_text(encoding='utf-8'),['pipeline_normalizado'])
code('''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from time import perf_counter
from statistics import median
import hashlib

raiz = Path.cwd()
origem = raiz / "saude_mulher_dhs.db"
destino = raiz / "saude_mulher_normalizado.db"
def sha256(arquivo):
    h=hashlib.sha256()
    with arquivo.open('rb') as f:
        for bloco in iter(lambda: f.read(4*1024*1024), b''): h.update(bloco)
    return h.hexdigest()
hash_origem = sha256(origem)
t0=perf_counter()
construir_banco(origem,destino)
print(f"Carga normalizada concluída em {perf_counter()-t0:.2f} s.")
assert sha256(origem)==hash_origem, "A origem deve permanecer intacta."
conn=sqlite3.connect(destino)
conn.execute('PRAGMA foreign_keys=ON')
def consulta(sql, amostra=False):
    tabela=pd.read_sql_query(sql,conn)
    if amostra:
        display(tabela.groupby('pais_codigo',sort=True).size().rename('registros_selecionados').reset_index())
        display(tabela.groupby('pais_codigo',sort=True).head(1).sort_values('pais_codigo'))
        print(f"{len(tabela):,} linhas consultadas; exibição de um exemplo por país presente.")
    else:
        display(tabela)
    return tabela

resumo=pd.DataFrame([(t,conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0])
                    for t in ['Pais','Levantamento','Domicilio','Mulher','Entrevista','Nascimento','Crianca','Morador','Metodo','Conhecimento_Metodo']],
                   columns=['relacao','registros'])
display(resumo)
assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
assert conn.execute('SELECT COUNT(*) FROM Mulher').fetchone()[0]==407600
assert conn.execute('SELECT COUNT(*) FROM Crianca').fetchone()[0]==282641
assert conn.execute('SELECT COUNT(*) FROM Morador').fetchone()[0]==1884683
assert conn.execute("SELECT COUNT(*) FROM Nascimento WHERE origem='BR'").fetchone()[0]==877412
assert conn.execute("SELECT COUNT(*) FROM Nascimento WHERE origem='KR_sem_BR'").fetchone()[0]==53333
assert conn.execute("SELECT COUNT(*) FROM Domicilio WHERE origem='IR_sem_HR'").fetchone()[0]==5189
print('PK/FK, integridade e contagens de origem validadas; hash da origem preservado.')''')
code('''cobertura=consulta("""
SELECT p.codigo,p.nome,l.fase, MIN(e.ano) AS ano_min,MAX(e.ano) AS ano_max,
       COUNT(*) AS mulheres,
       SUM(e.usa_metodo IS NOT NULL) AS resposta_contraceptiva,
       SUM(d.riqueza IS NOT NULL) AS riqueza_disponivel,
       SUM(d.origem='HR') AS mulheres_com_HR
FROM Entrevista e JOIN Mulher m ON m.id=e.mulher_id
JOIN Domicilio d ON d.id=m.domicilio_id
JOIN Levantamento l ON l.id=d.levantamento_id JOIN Pais p ON p.codigo=l.pais_codigo
GROUP BY p.codigo,p.nome,l.fase ORDER BY p.nome
""")
assert len(cobertura)==37
print('Todos os 37 países participam; compare também os anos e as ausências.')''')

md('''# 4. Diagrama ER

O diagrama corresponde às relações efetivamente carregadas. O modelo tem dez tipos de entidade/relação; País, Levantamento, Domicílio, Mulher, Nascimento e Método atendem folgadamente ao requisito de identificador mais dois atributos. Mulher conhece Método é **M:N**, materializado por `Conhecimento_Metodo`; os dois lados possuem múltiplos vínculos.''')
diagram(False)
code('''vinculos=consulta("""
SELECT (SELECT COUNT(*) FROM Conhecimento_Metodo WHERE nivel>0) AS vinculos_positivos,
       (SELECT COUNT(*) FROM (SELECT mulher_id FROM Conhecimento_Metodo WHERE nivel>0 GROUP BY mulher_id HAVING COUNT(*)>1)) AS mulheres_conhecem_varios,
       (SELECT COUNT(*) FROM (SELECT metodo_id FROM Conhecimento_Metodo WHERE nivel>0 GROUP BY metodo_id HAVING COUNT(*)>1)) AS metodos_conhecidos_por_varias
""")
assert vinculos.mulheres_conhecem_varios.iloc[0]>0 and vinculos.metodos_conhecidos_por_varias.iloc[0]==9''')
md('''# 5. Diagrama relacional

PK identifica a linha; FK exige que sua entidade referenciada exista. `Conhecimento_Metodo` tem PK composta; `Entrevista` usa a PK de Mulher e `Crianca` usa a PK de Nascimento. As chaves naturais também recebem `UNIQUE`. Campos desconhecidos permanecem NULL; os códigos brutos de saúde são preservados para evitar equiparar ausência a zero.''')
diagram(True)
code('''restricoes=consulta("""
SELECT name AS tabela, sql AS definicao_implementada
FROM sqlite_master WHERE type='table' ORDER BY name
""")''')
md('''# 6. Consultas, resultados e análise

Todas as consultas percorrem o conjunto de países disponível. Nas consultas 1 e 2, a SQL recupera todos os registros elegíveis; a exibição mostra contagens e um exemplo de **cada país presente**, sem privilegiar o primeiro arquivo. As demais tabelas mostram comparações agregadas, não as primeiras dez linhas de Angola.

**Perguntas sociais:** diferenças rurais persistem quando riqueza e escolaridade são comparáveis? O conhecimento de métodos acompanha o uso? A cobertura do pré-natal apresenta gradientes de riqueza semelhantes entre países? A ausência de dados pode distorcer a ordem dos países?''')

base="FROM Entrevista e JOIN Mulher m ON m.id=e.mulher_id JOIN Domicilio d ON d.id=m.domicilio_id JOIN Levantamento l ON l.id=d.levantamento_id JOIN Pais p ON p.codigo=l.pais_codigo"
queries=[
('6.1.1','Seleção e projeção: adolescentes de 15–19 anos sem escolaridade. A identificação técnica começa pelo código do país; somente Mulher é consultada.',"SELECT substr(id,1,2) AS pais_codigo,id AS mulher_id,idade,idade_primeiro_nascimento,filhos_nascidos_vivos FROM Mulher WHERE idade BETWEEN 15 AND 19 AND escolaridade=0 ORDER BY id",True),
('6.1.2','Seleção e projeção: domicílios rurais no quintil mais pobre, sem eletricidade. Ausência de HR não conta como ausência de eletricidade.',"SELECT substr(id,1,2) AS pais_codigo,id AS domicilio_id,fonte_agua,membros FROM Domicilio WHERE residencia=2 AND riqueza=1 AND eletricidade=0 ORDER BY id",True),
('6.2.1','Junção de duas relações (Mulher–Domicilio): composição demográfica rural e urbana em cada país. Média de filhos é descritiva e não uma taxa de fecundidade.',"""SELECT substr(d.id,1,2) AS pais_codigo,CASE d.residencia WHEN 1 THEN 'Urbano' WHEN 2 THEN 'Rural' END AS residencia,
COUNT(*) AS mulheres,ROUND(AVG(m.idade),2) AS idade_media,
ROUND(AVG(m.filhos_nascidos_vivos),2) AS filhos_medios,
ROUND(100.0*SUM(m.escolaridade=0)/NULLIF(SUM(m.escolaridade IS NOT NULL),0),2) AS percentual_sem_escola
FROM Mulher m JOIN Domicilio d ON d.id=m.domicilio_id WHERE d.residencia IN(1,2)
GROUP BY substr(d.id,1,2),d.residencia ORDER BY pais_codigo,d.residencia""",False),
('6.2.2','Junção de duas relações (Entrevista–Mulher): uso de algum contraceptivo por nível de escolaridade em cada país. O denominador usa resposta válida e peso positivo.',"""SELECT substr(m.id,1,2) AS pais_codigo,m.escolaridade,COUNT(*) AS respostas_validas,
ROUND(100.0*SUM(e.peso*e.usa_metodo)/SUM(e.peso),2) AS percentual_uso_ponderado
FROM Entrevista e JOIN Mulher m ON m.id=e.mulher_id
WHERE e.usa_metodo IS NOT NULL AND e.peso>0 AND m.escolaridade IS NOT NULL
GROUP BY substr(m.id,1,2),m.escolaridade ORDER BY pais_codigo,m.escolaridade""",False),
('6.2.3','Junção de duas relações (Conhecimento_Metodo–Metodo): conhecimento dos nove métodos por país. Cada denominador contém quem respondeu àquele método; percentuais não ponderados, pois esta categoria usa somente duas relações.',"""SELECT substr(k.mulher_id,1,2) AS pais_codigo,t.nome,t.classe,COUNT(*) AS respostas_validas,
SUM(k.nivel>0) AS conhecem,ROUND(100.0*SUM(k.nivel>0)/COUNT(*),2) AS percentual_conhecimento
FROM Conhecimento_Metodo k JOIN Metodo t ON t.id=k.metodo_id
GROUP BY substr(k.mulher_id,1,2),t.id,t.nome,t.classe ORDER BY pais_codigo,t.id""",False),
('6.3.1','Junção de cinco relações: pobreza material e escolaridade por país e residência, para distinguir composição socioeconômica de diferenças de saúde.',f"""SELECT p.codigo,p.nome,CASE d.residencia WHEN 1 THEN 'Urbano' WHEN 2 THEN 'Rural' END AS residencia,
COUNT(*) AS mulheres,ROUND(100.0*SUM(d.riqueza=1)/NULLIF(SUM(d.riqueza IS NOT NULL),0),2) AS percentual_quintil_1,
ROUND(100.0*SUM(d.eletricidade=0)/NULLIF(SUM(d.eletricidade IS NOT NULL),0),2) AS percentual_sem_eletricidade,
ROUND(100.0*SUM(m.escolaridade=0)/NULLIF(SUM(m.escolaridade IS NOT NULL),0),2) AS percentual_sem_escola
{base} WHERE d.residencia IN(1,2) GROUP BY p.codigo,p.nome,d.residencia ORDER BY p.nome,d.residencia""",False),
('6.3.2','Junção de seis relações: disponibilidade da informação de pré-natal em nascimentos recentes. A análise usa somente o nascimento mais recente (índice 1), ocorrido nos 60 meses anteriores à entrevista, e distingue códigos ausentes/especiais.',f"""SELECT p.codigo,p.nome,CASE d.residencia WHEN 1 THEN 'Urbano' WHEN 2 THEN 'Rural' END AS residencia,
COUNT(*) AS nascimentos_recentes,SUM(n.consultas_prenatal_codigo BETWEEN 0 AND 90) AS respostas_validas,
ROUND(100.0*SUM(n.consultas_prenatal_codigo BETWEEN 0 AND 90)/COUNT(*),2) AS cobertura_resposta_percentual
{base} JOIN Nascimento n ON n.mulher_id=m.id
WHERE n.indice=1 AND e.data_cmc-n.data_cmc BETWEEN 0 AND 59 AND d.residencia IN(1,2)
GROUP BY p.codigo,p.nome,d.residencia ORDER BY p.nome,d.residencia""",False),
('6.3.3','Junção de cinco relações com o M:N e catálogo: conhecimento de ao menos um dos sete métodos modernos do recorte e uso atual de qualquer método. Usamos uma linha por mulher para impedir que quem conhece vários métodos seja contado várias vezes. A diferença entre indicadores não identifica individualmente demanda não atendida.',f"""WITH conhecimento AS (
SELECT k.mulher_id,MAX(k.nivel>0) AS conhece_moderno
FROM Conhecimento_Metodo k JOIN Metodo t ON t.id=k.metodo_id WHERE t.classe='Moderno' GROUP BY k.mulher_id)
SELECT p.codigo,p.nome,COUNT(*) AS mulheres_respostas_validas,
ROUND(100.0*SUM(e.peso*k.conhece_moderno)/SUM(e.peso),2) AS percentual_conhece_moderno,
ROUND(100.0*SUM(e.peso*e.usa_metodo)/SUM(e.peso),2) AS percentual_uso_qualquer
{base} JOIN conhecimento k ON k.mulher_id=m.id
WHERE e.usa_metodo IS NOT NULL AND e.peso>0
GROUP BY p.codigo,p.nome ORDER BY p.nome""",False),
('6.4.1','Agregação sobre cinco relações: uso contraceptivo por país, residência, quintil de riqueza e escolaridade. Essa tabela fornece os estratos para separar composição socioeconômica da diferença rural–urbana.',f"""SELECT p.codigo,p.nome,d.residencia,d.riqueza,m.escolaridade,COUNT(*) AS n,
SUM(e.peso) AS peso_total,SUM(e.peso*e.usa_metodo) AS peso_uso
{base} WHERE e.usa_metodo IS NOT NULL AND e.peso>0 AND d.residencia IN(1,2)
AND d.riqueza BETWEEN 1 AND 5 AND m.escolaridade BETWEEN 0 AND 3
GROUP BY p.codigo,p.nome,d.residencia,d.riqueza,m.escolaridade ORDER BY p.nome,d.residencia,d.riqueza,m.escolaridade""",False),
('6.4.2','Agregação sobre seis relações: pré-natal de quatro ou mais consultas por país, residência e riqueza. O denominador clínico considera somente o nascimento mais recente nos últimos 60 meses com resposta válida; a cobertura aparece separadamente.',f"""SELECT p.codigo,p.nome,d.residencia,d.riqueza,COUNT(*) AS nascimentos_recentes,
SUM(n.consultas_prenatal_codigo BETWEEN 0 AND 90) AS n_validos,
SUM(CASE WHEN n.consultas_prenatal_codigo BETWEEN 0 AND 90 THEN e.peso ELSE 0 END) AS peso_valido,
SUM(CASE WHEN n.consultas_prenatal_codigo BETWEEN 4 AND 90 THEN e.peso ELSE 0 END) AS peso_quatro_mais
{base} JOIN Nascimento n ON n.mulher_id=m.id
WHERE n.indice=1 AND e.data_cmc-n.data_cmc BETWEEN 0 AND 59 AND e.peso>0
AND d.residencia IN(1,2) AND d.riqueza BETWEEN 1 AND 5
GROUP BY p.codigo,p.nome,d.residencia,d.riqueza ORDER BY p.nome,d.residencia,d.riqueza""",False)]
for i,(section,descr,sql,amostra) in enumerate(queries,1):
    if i in [1,3,6,9]: md({1:'## 6.1 Duas consultas com seleção e projeção',3:'## 6.2 Três consultas com junção de duas relações',6:'## 6.3 Três consultas com junção de três ou mais relações',9:'## 6.4 Duas consultas com agregação sobre junção'}[i])
    md(f'### {section} Consulta {i}\n\n{descr}')
    code(f'sql_{i} = """\n{sql}\n"""\nr{i} = consulta(sql_{i}, amostra={amostra})')
    if i in [1,2]:
        code(f'''display(Markdown(f"**Leitura:** a consulta {i} encontrou {{len(r{i}):,}} registros elegíveis em {{r{i}.pais_codigo.nunique()}} países. As contagens são da amostra; diferenças no tamanho das pesquisas impedem comparar os totais como prevalências."))''')
    elif i==3:
        code('''comparacao=r3.pivot(index='pais_codigo',columns='residencia',values='percentual_sem_escola').dropna()
maior=(comparacao.Rural>comparacao.Urbano).sum()
display(Markdown(f"**Leitura:** a proporção não ponderada de mulheres sem escola é maior no meio rural em {maior} de {len(comparacao)} países com ambas as áreas. Essa composição deve ser considerada antes de atribuir as diferenças contraceptivas apenas ao território."))''')
    elif i==4:
        code('''extremos=r4[r4.escolaridade.isin([0,3])].pivot(index='pais_codigo',columns='escolaridade',values='percentual_uso_ponderado').dropna()
display(Markdown(f"**Leitura:** entre os {len(extremos)} países com respostas nos dois extremos de escolaridade, {int((extremos[3]>extremos[0]).sum())} apresentam maior uso ponderado no nível superior do que entre mulheres sem escola. Idade, estado conjugal, preferências reprodutivas e acesso podem explicar parte da associação."))''')
    elif i==5:
        code('''display(Markdown(f"**Leitura:** o M:N contém respostas válidas em {r5.pais_codigo.nunique()} países. As categorias de conhecimento variam na cobertura; não comparar a soma de todos os métodos como se fosse número de mulheres nem presumir que conhecimento resulta em uso."))''')
    elif i==6:
        code('''material=r6.pivot(index='codigo',columns='residencia',values='percentual_sem_eletricidade').dropna()
display(Markdown(f"**Leitura:** a falta de eletricidade é mais frequente no meio rural em {int((material.Rural>material.Urbano).sum())} de {len(material)} países com informação nas duas áreas. O Sudão não possui HR neste recorte e não entra nessa comparação habitacional; seu dado ausente não é eletricidade presente."))''')
    elif i==7:
        code('''display(Markdown(f"**Leitura:** há nascimentos recentes em {r7.codigo.nunique()} países. A cobertura de respostas válidas de pré-natal varia de {r7.cobertura_resposta_percentual.min():.1f}% a {r7.cobertura_resposta_percentual.max():.1f}% entre os grupos país–residência. Um percentual de atendimento aparentemente alto pode descrever apenas a parte com informação registrada."))''')
    elif i==8:
        code('''r8['diferenca_pp']=r8.percentual_conhece_moderno-r8.percentual_uso_qualquer
display(r8[['nome','mulheres_respostas_validas','diferenca_pp']])
display(Markdown(f"**Leitura:** conhecimento moderno e uso de qualquer método diferem em magnitude entre {len(r8)} países. O descompasso sugere investigar barreiras e preferências, mas os indicadores têm conceitos diferentes e não medem necessidade não atendida."))''')

md('''## 6.5 Cruzamentos entre países e visualizações

**Contracepção: diferença bruta e padronizada.** Para cada país da consulta 9, formamos estratos riqueza × escolaridade com pelo menos 30 respostas válidas em **cada** área. Usamos somente o suporte comum rural/urbano. Calculamos taxas ponderadas dentro dos estratos e aplicamos, às duas áreas, a mesma distribuição conjunta de riqueza e escolaridade (pesos combinados do próprio país). A diferença padronizada não é efeito causal.

Comparamos a diferença bruta **nessa mesma subamostra**, antes da padronização, com a diferença padronizada. Assim, uma eventual inversão não decorre apenas de excluir estratos de uma das versões. A participação do suporte comum em cada área é mostrada; países sem suporte suficiente permanecem explicitamente ausentes.''')
code('''ajustes=[]
for (codigo,nome),g in r9.groupby(['codigo','nome']):
    n=g.pivot(index=['riqueza','escolaridade'],columns='residencia',values='n')
    suporte=n.index[(n.get(1,0)>=30)&(n.get(2,0)>=30)]
    if len(suporte)==0: continue
    sub=g.set_index(['riqueza','escolaridade']).loc[suporte].reset_index()
    wt=sub.pivot(index=['riqueza','escolaridade'],columns='residencia',values='peso_total')
    uso=sub.pivot(index=['riqueza','escolaridade'],columns='residencia',values='peso_uso')
    padrao=(wt[1]+wt[2]); padrao=padrao/padrao.sum()
    bruto=100*(uso[1].sum()/wt[1].sum()-uso[2].sum()/wt[2].sum())
    ajustado=100*((uso[1]/wt[1]-uso[2]/wt[2])*padrao).sum()
    totais=g.groupby('residencia').peso_total.sum()
    ajustes.append([codigo,nome,len(suporte),bruto,ajustado,
                    100*wt[1].sum()/totais[1],100*wt[2].sum()/totais[2]])
ajustes=pd.DataFrame(ajustes,columns=['codigo','pais','estratos','bruta_pp','padronizada_pp','suporte_urbano_pct','suporte_rural_pct'])
ajustes['inversao']=ajustes.bruta_pp*ajustes.padronizada_pp<0
ajustes=ajustes.sort_values('padronizada_pp')
display(ajustes.round(2))
ausentes=sorted(set(cobertura.codigo)-set(ajustes.codigo))
print('Países sem suporte comum suficiente:', ', '.join(ausentes) or 'nenhum')
fig,ax=plt.subplots(figsize=(11,max(7,len(ajustes)*.28)))
y=np.arange(len(ajustes))
ax.hlines(y,ajustes.bruta_pp,ajustes.padronizada_pp,color='#a0b0bc')
ax.scatter(ajustes.bruta_pp,y,label='Bruta no suporte comum',color='#aa687c')
ax.scatter(ajustes.padronizada_pp,y,label='Padronizada: riqueza e escolaridade',color='#1a7a8c')
ax.set_yticks(y,ajustes.pais); ax.axvline(0,color='gray',lw=.7)
ax.set_xlabel('Uso urbano − rural (pontos percentuais)'); ax.set_title('O contexto socioeconômico explica toda a diferença territorial?')
ax.legend(loc='best'); ax.grid(axis='x',alpha=.2); fig.tight_layout(); display(fig); plt.close(fig)
inversoes=ajustes[ajustes.inversao]
maiores=ajustes.assign(mudanca=(ajustes.bruta_pp-ajustes.padronizada_pp).abs()).nlargest(3,'mudanca')
display(Markdown(f"**Achado:** {len(ajustes)} países têm suporte comum. Em {int((ajustes.padronizada_pp>0).sum())}, o uso urbano permanece maior após padronizar riqueza e escolaridade. Houve {len(inversoes)} inversões de sinal entre a comparação bruta e padronizada na mesma subamostra; " +
                ("países: "+', '.join(inversoes.pais)+'. ' if len(inversoes) else "não se demonstrou inversão de sinal. ")+ 
                "As maiores mudanças em magnitude aparecem em "+', '.join(maiores.pais)+". Isso mostra por que uma média conjunta pode esconder mecanismos diferentes entre países."))''')
code('''# Gradiente de pré-natal por país e riqueza, sem misturar pesos de países diferentes.
prenatal=r10.groupby(['codigo','nome','riqueza'],as_index=False)[['nascimentos_recentes','n_validos','peso_valido','peso_quatro_mais']].sum()
prenatal['percentual']=100*prenatal.peso_quatro_mais/prenatal.peso_valido.replace(0,np.nan)
prenatal['cobertura_pct']=100*prenatal.n_validos/prenatal.nascimentos_recentes
# Transparência: células com menos de 30 respostas não são comparadas no mapa.
prenatal.loc[prenatal.n_validos<30,'percentual']=np.nan
matriz=prenatal.pivot(index='nome',columns='riqueza',values='percentual').reindex(cobertura.nome.sort_values())
fig,ax=plt.subplots(figsize=(9,12))
cmap=plt.get_cmap('YlGnBu').copy(); cmap.set_bad('#dddddd')
im=ax.imshow(matriz.to_numpy(),vmin=0,vmax=100,cmap=cmap,aspect='auto')
ax.set_yticks(np.arange(len(matriz)),matriz.index); ax.set_xticks(np.arange(5),['Mais pobre','2','3','4','Mais rico'])
for row in range(len(matriz)):
    for col in range(5):
        value=matriz.iloc[row,col]
        if pd.notna(value): ax.text(col,row,f'{value:.0f}',ha='center',va='center',fontsize=7,color='white' if value>65 else 'black')
ax.set_title('Pré-natal ≥4 consultas: todos os países, por quintil de riqueza\\nÚltimo nascimento recente; cinza = informação insuficiente')
fig.colorbar(im,ax=ax,label='% ponderado entre respostas válidas'); fig.tight_layout(); display(fig); plt.close(fig)
gradiente=matriz[[1,5]].dropna().copy(); gradiente['diferenca_pp']=gradiente[5]-gradiente[1]
display(gradiente.sort_values('diferenca_pp').round(2))
coverage=prenatal.groupby('nome')[['n_validos','nascimentos_recentes']].sum()
coverage['cobertura_pct']=100*coverage.n_validos/coverage.nascimentos_recentes
display(coverage.round(2))
display(Markdown(f"**Achado:** em {int((gradiente.diferenca_pp>0).sum())} dos {len(gradiente)} países com pelo menos 30 respostas nos dois quintis extremos, o quintil mais rico apresenta maior percentual de quatro consultas. A diferença varia de {gradiente.diferenca_pp.min():.1f} a {gradiente.diferenca_pp.max():.1f} pontos percentuais. Países e estratos com baixa cobertura não devem ser ordenados como se o indicador tivesse a mesma completude em todos eles."))''')
md('''**Interpretação conjunta e inovação social:** as tabelas e gráficos mostram que território, riqueza e escolaridade precisam ser analisados conjuntamente. Uma diferença rural pequena pode coexistir com baixo uso nas duas áreas; uma grande vantagem urbana pode diminuir quando comparamos perfis socioeconômicos semelhantes. Para priorização, é necessário examinar simultaneamente o nível do indicador, o gradiente, o tamanho da amostra e a cobertura. Conhecimento sem uso não comprova falta de acesso, e mais consultas não comprova qualidade clínica.

Os resultados indicam hipóteses para ações e pesquisa — ampliar acesso rural, informação e condições materiais conforme o contexto — mas não identificam políticas públicas bem-sucedidas sem séries temporais, desenho causal e evidência externa. Essa distinção mantém as descobertas úteis e verificáveis.''')

md('''## 6.6 Otimização — ponto extra de até 20%

**Estratégia:** índice composto de filtro e cobertura em Entrevista para recuperar respostas positivas/negativas em um ano de entrevista, com a chave de junção no mesmo índice. A consulta seleciona o ano mais frequente do conjunto completo e cruza os países; o filtro tem uma razão analítica: comparar pesquisas de um mesmo período em vez de tratar anos diferentes como simultâneos.

Comparamos o **mesmo SQL, dados e resultado** antes e depois do índice. Fazemos uma execução de aquecimento e sete medições completas (`fetchall`) em cada versão; usamos a mediana. Mantemos cache e ambiente como limitações, mostramos as medidas individuais e os planos `EXPLAIN QUERY PLAN`. Os índices de PK/FK permanecem nas duas versões; não removemos integridade para produzir ganho artificial. A execução repetida remove somente o índice experimental no banco derivado.''')
code('''conn.execute('DROP INDEX IF EXISTS idx_entrevista_ano_uso')
ano=conn.execute('SELECT ano FROM Entrevista WHERE ano IS NOT NULL GROUP BY ano ORDER BY COUNT(*) DESC LIMIT 1').fetchone()[0]
sql_otimizacao="""
SELECT p.nome,m.escolaridade,COUNT(*) AS n,SUM(e.peso) AS peso
FROM Entrevista e JOIN Mulher m ON m.id=e.mulher_id
JOIN Domicilio d ON d.id=m.domicilio_id
JOIN Levantamento l ON l.id=d.levantamento_id JOIN Pais p ON p.codigo=l.pais_codigo
WHERE e.ano=? AND e.usa_metodo=1
GROUP BY p.nome,m.escolaridade ORDER BY p.nome,m.escolaridade
"""
def medir():
    esperado=conn.execute(sql_otimizacao,(ano,)).fetchall() # aquecimento
    tempos=[]
    for _ in range(7):
        t=perf_counter(); obtido=conn.execute(sql_otimizacao,(ano,)).fetchall(); tempos.append(perf_counter()-t)
        assert obtido==esperado
    return esperado,tempos
antes,tempos_antes=medir()
plano_antes=pd.read_sql_query('EXPLAIN QUERY PLAN '+sql_otimizacao,conn,params=(ano,))
t=perf_counter()
conn.execute('CREATE INDEX idx_entrevista_ano_uso ON Entrevista(ano,usa_metodo,mulher_id,peso)')
conn.commit(); custo_indice=perf_counter()-t
depois,tempos_depois=medir()
plano_depois=pd.read_sql_query('EXPLAIN QUERY PLAN '+sql_otimizacao,conn,params=(ano,))
assert antes==depois, 'A otimização deve preservar os resultados.'
assert any('idx_entrevista_ano_uso' in str(x) for x in plano_depois.detail)
display(Markdown(f'**Ano filtrado: {ano}. Plano antes:**')); display(plano_antes)
display(Markdown('**Plano depois:**')); display(plano_depois)
display(pd.DataFrame({'execucao':range(1,8),'antes_ms':np.array(tempos_antes)*1000,'depois_ms':np.array(tempos_depois)*1000}))
med_antes,med_depois=median(tempos_antes),median(tempos_depois)
ganho=100*(1-med_depois/med_antes)
display(Markdown(f"**Resultado medido:** mediana de {med_antes*1000:.2f} ms antes e {med_depois*1000:.2f} ms depois; redução de {ganho:.1f}% e razão de {med_antes/med_depois:.2f}×. Criar o índice custou {custo_indice:.2f} s. O índice acelera este filtro, ocupa espaço e adiciona custo à carga; o ganho não vale automaticamente para todas as dez consultas."))
conn.execute('ANALYZE'); conn.commit()
print('Banco derivado final com índice e estatísticas; resultados equivalentes confirmados.')''')
md('''## 6.7 Verificação dos requisitos

| Critério | Evidência neste notebook |
|---|---|
| Tema de saúde da mulher — extra | IR, contracepção, desigualdades e pré-natal |
| Origem não SQL e reprodução | Stata DHS, portal/API, catálogo, manifesto e scripts — seção 3 |
| Processo bottom-up e normalização | Dependências funcionais, decomposição e carga executável — seção 3 |
| ≥4 entidades com identificador e ≥2 atributos | Pais, Levantamento, Domicilio, Mulher, Nascimento, Metodo |
| ≥3 relacionamentos, incluindo M:N | FKs dos diagramas e Conhecimento_Metodo carregado e validado |
| Diagramas anexados | Imagens incorporadas nas seções 4 e 5 |
| 2 seleção/projeção | Consultas 1–2 |
| 3 junções de duas relações | Consultas 3–5 |
| 3 junções de três ou mais relações | Consultas 6–8 |
| 2 agregações sobre junções | Consultas 9–10 |
| Análise e gráficos | Cobertura, níveis, gradientes e padronização em todos os países — seção 6.5 |
| Otimização — extra de até 20% | Índice, planos, tempos repetidos e equivalência — seção 6.6 |
| Autoavaliação individual | Campos abaixo, a serem preenchidos pelos integrantes |

A pontuação depende da avaliação e apresentação; as evidências acima demonstram a implementação, sem garantir a nota. Os demais dois pontos de exercícios/participação dependem das atividades da disciplina e não podem ser produzidos ou comprovados por este notebook.''')
md('''# 7. Autoavaliação dos membros

Por decisão do grupo nesta conversa, as atividades individuais permanecem pendentes até confirmação dos integrantes.

| Membro | Atividades realizadas | Autoavaliação |
|---|---|---|
| Henrique Lima Gusmão | A informar pelo integrante | A preencher |
| Felipe Pires Franco | A informar pelo integrante | A preencher |
| Izabella Galdino Correia | A informar pelo integrante | A preencher |
| Alice Lina Oliveira da Silva | A informar pelo integrante | A preencher |

Antes da entrega: completar as três matrículas faltantes, atividades e autoavaliações; revisar coletivamente interpretações e exportar o notebook para PDF. Todos devem participar da apresentação de até seis minutos.''')
code('''conn.close()
assert sha256(origem)==hash_origem
print('Execução finalizada: origem preservada e banco normalizado salvo.')''')

# Execute and capture standard notebook outputs, including figures.
for i,cell in enumerate(cells):
    if cell['cell_type']=='code': compile(''.join(cell['source']),f'cell_syntax_{i}','exec')
ns={}; count=0
def capture(value):
    if isinstance(value,plt.Figure):
        buf=io.BytesIO(); value.savefig(buf,format='png',dpi=130,bbox_inches='tight')
        data={'image/png':base64.b64encode(buf.getvalue()).decode(),'text/plain':'Gráfico comparativo dos países'}
    elif hasattr(value,'to_html'):
        data={'text/html':value.to_html(index=True),'text/plain':value.to_string()}
    elif hasattr(value,'_repr_markdown_'):
        data={'text/markdown':value._repr_markdown_(),'text/plain':value._repr_markdown_()}
    else: data={'text/plain':repr(value)}
    outputs.append({'output_type':'display_data','metadata':{},'data':data})

for cell in cells:
    if cell['cell_type']!='code': continue
    count+=1; outputs=[]; stdout=io.StringIO()
    source=''.join(cell['source']).replace('from IPython.display import display, Markdown','from IPython.display import Markdown')
    ns['display']=capture
    print(f'Running cell {count}: {source.splitlines()[0][:90]}',flush=True)
    with contextlib.redirect_stdout(stdout): exec(compile(source,f'cell_{count}','exec'),ns)
    if stdout.getvalue(): outputs.append({'output_type':'stream','name':'stdout','text':stdout.getvalue()})
    cell['execution_count']=count; cell['outputs']=outputs

nb['cells']=cells; nb['nbformat_minor']=5
for i,c in enumerate(cells): c['id']=f'dhs-normalizado-{i:03d}'
nb['metadata']['language_info']['version']='3.14.3'
(ROOT/'tp_template.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(f'Saved {len(cells)} cells, {count} executed cells.',flush=True)
print(ns['ajustes'].round(2).to_string(index=False),flush=True)
print(f'Optimization: {ns["ganho"]:.2f}%',flush=True)
