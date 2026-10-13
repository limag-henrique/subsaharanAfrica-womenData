"""Suporte à seção 3 do notebook DHS.

Mantém a carga normalizada e a apresentação fora do texto do relatório.
O recorte analítico usa entrevistas femininas; moradores e crianças dão
contexto familiar. Pesquisas suplementares conservam suas próprias chaves.
"""

from pathlib import Path
import os
import sqlite3


def construir_banco(origem, destino, suplementos=()):
    """Transforma o núcleo DHS em relações com PK/FK, sem alterar a origem."""
    origem, destino = Path(origem).resolve(), Path(destino).resolve()
    if origem == destino:
        raise ValueError('Origem e destino devem ser diferentes.')
    temporario = destino.with_suffix('.tmp.db')
    if temporario.exists():
        temporario.unlink()
    c = sqlite3.connect(temporario, uri=True)
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('ATTACH DATABASE ? AS fonte', (origem.as_uri()+'?mode=ro',))
    dom = "levantamento_id || '|' || CAST(v001 AS INTEGER) || '|' || CAST(v002 AS INTEGER)"
    mulher = dom + " || '|' || CAST(v003 AS INTEGER)"
    nasc = mulher + " || '|' || CAST(bidx AS INTEGER)"
    try:
        c.executescript('''
        CREATE TABLE Pais(codigo TEXT PRIMARY KEY, nome TEXT NOT NULL UNIQUE);
        CREATE TABLE Levantamento(id TEXT PRIMARY KEY, pais_codigo TEXT NOT NULL REFERENCES Pais(codigo), fase TEXT NOT NULL, UNIQUE(pais_codigo,fase));
        CREATE TABLE Domicilio(
          id TEXT PRIMARY KEY, levantamento_id TEXT NOT NULL REFERENCES Levantamento(id),
          cluster INTEGER NOT NULL, numero INTEGER NOT NULL, regiao INTEGER,
          residencia INTEGER CHECK(residencia IN(1,2)), riqueza INTEGER CHECK(riqueza BETWEEN 1 AND 5),
          eletricidade INTEGER CHECK(eletricidade IN(0,1)), fonte_agua INTEGER, membros INTEGER,
          origem TEXT NOT NULL CHECK(origem IN('HR','IR_sem_HR','IR_completo')),
          UNIQUE(levantamento_id,cluster,numero));
        CREATE TABLE Mulher(
          id TEXT PRIMARY KEY, domicilio_id TEXT NOT NULL REFERENCES Domicilio(id), linha INTEGER NOT NULL,
          idade INTEGER, escolaridade INTEGER CHECK(escolaridade BETWEEN 0 AND 3),
          filhos_nascidos_vivos INTEGER, idade_primeiro_nascimento INTEGER,
          UNIQUE(domicilio_id,linha));
        CREATE TABLE Entrevista(
          mulher_id TEXT PRIMARY KEY REFERENCES Mulher(id), ano INTEGER, mes INTEGER,
          data_cmc INTEGER, peso REAL CHECK(peso>0), usa_metodo INTEGER CHECK(usa_metodo IN(0,1)),
          coorte TEXT NOT NULL CHECK(coorte IN('nucleo_e_contracepcao','nucleo_exclusivo','contracepcao')));
        CREATE TABLE Nascimento(
          id TEXT PRIMARY KEY, mulher_id TEXT NOT NULL REFERENCES Mulher(id), indice INTEGER NOT NULL CHECK(indice>=1),
          ano INTEGER, mes INTEGER, data_cmc INTEGER, sexo INTEGER CHECK(sexo IN(1,2)), vivo INTEGER CHECK(vivo IN(0,1)),
          consultas_prenatal_codigo INTEGER, local_parto_codigo INTEGER, cesarea_codigo INTEGER,
          assistencia_medico_codigo INTEGER, assistencia_m3b_codigo INTEGER,
          origem TEXT NOT NULL CHECK(origem IN('BR','KR_sem_BR')), UNIQUE(mulher_id,indice));
        CREATE TABLE Crianca(
          nascimento_id TEXT PRIMARY KEY REFERENCES Nascimento(id), idade_anos INTEGER,
          diarreia_codigo INTEGER, cartao_vacina_codigo INTEGER);
        CREATE TABLE Morador(
          id TEXT PRIMARY KEY, domicilio_id TEXT NOT NULL REFERENCES Domicilio(id), linha INTEGER NOT NULL,
          sexo INTEGER, idade INTEGER, escolaridade_codigo INTEGER, relacao_chefe_codigo INTEGER,
          UNIQUE(domicilio_id,linha));
        CREATE TABLE Metodo(
          id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE, classe TEXT NOT NULL CHECK(classe IN('Moderno','Tradicional')));
        CREATE TABLE Conhecimento_Metodo(
          mulher_id TEXT NOT NULL REFERENCES Mulher(id), metodo_id INTEGER NOT NULL REFERENCES Metodo(id),
          nivel INTEGER NOT NULL CHECK(nivel BETWEEN 0 AND 7), PRIMARY KEY(mulher_id,metodo_id)) WITHOUT ROWID;
        INSERT INTO Pais SELECT pais_codigo,nome_pais FROM fonte.Pais;
        INSERT INTO Levantamento SELECT levantamento_id,pais_codigo,fase FROM fonte.Levantamento;
        INSERT INTO Domicilio
        SELECT levantamento_id||'|'||CAST(hv001 AS INTEGER)||'|'||CAST(hv002 AS INTEGER),
               levantamento_id,hv001,hv002,hv024,
               CASE WHEN hv025 IN(1,2) THEN hv025 END,
               CASE WHEN hv270 BETWEEN 1 AND 5 THEN hv270 END,
               CASE WHEN hv206 IN(0,1) THEN hv206 END,hv201,hv009,'HR'
        FROM fonte.Domicilio;
        ''')
        c.execute(f'''INSERT OR IGNORE INTO Domicilio
        SELECT {dom},levantamento_id,v001,v002,MAX(v024),
               MAX(CASE WHEN v025 IN(1,2) THEN v025 END),
               MAX(CASE WHEN v190 BETWEEN 1 AND 5 THEN v190 END),
               NULL,NULL,NULL,'IR_sem_HR'
        FROM fonte.Mulher GROUP BY levantamento_id,v001,v002''')
        c.execute(f'''INSERT INTO Mulher
        SELECT {mulher},{dom},v003,v012,
               CASE WHEN v106 BETWEEN 0 AND 3 THEN v106 END,v201,
               CASE WHEN v212 BETWEEN 10 AND 49 THEN v212 END
        FROM fonte.Mulher''')
        c.execute(f'''INSERT INTO Entrevista
        SELECT {mulher},CASE WHEN v007 BETWEEN 0 AND 99 THEN
               CASE WHEN v008>0 THEN 1900+CAST((v008-1)/12 AS INTEGER) END ELSE v007 END,v006,v008,
               CASE WHEN v005>0 THEN v005/1000000.0 END,
               CASE WHEN v312=0 THEN 0 WHEN v312 BETWEEN 1 AND 19 THEN 1 END,'nucleo_e_contracepcao'
        FROM fonte.Mulher''')
        for tabela, origem_registro in [('Nascimento','BR'),('Crianca','KR_sem_BR')]:
            assistencia='m3a,m3b' if tabela=='Nascimento' else 'NULL,NULL'
            c.execute(f'''INSERT OR IGNORE INTO Nascimento
            SELECT {nasc},{mulher},bidx,CASE WHEN b2 BETWEEN 0 AND 99 THEN
                   CASE WHEN b3>0 THEN 1900+CAST((b3-1)/12 AS INTEGER) END ELSE b2 END,b1,b3,
                   CASE WHEN b4 IN(1,2) THEN b4 END,
                   CASE WHEN b5 IN(0,1) THEN b5 END,
                   m14,m15,m17,{assistencia},?
            FROM fonte.{tabela}''',(origem_registro,))
        c.execute(f'''INSERT INTO Crianca
        SELECT {nasc},b8,h11,h1 FROM fonte.Crianca''')
        c.execute('''INSERT INTO Morador
        SELECT levantamento_id||'|'||CAST(hv001 AS INTEGER)||'|'||CAST(hv002 AS INTEGER)||'|'||CAST(hvidx AS INTEGER),
               levantamento_id||'|'||CAST(hv001 AS INTEGER)||'|'||CAST(hv002 AS INTEGER),
               hvidx,hv104,hv105,hv106,hv101 FROM fonte.Morador''')
        c.executemany('INSERT INTO Metodo VALUES(?,?,?)',[
            (1,'Pílula','Moderno'),(2,'DIU','Moderno'),(3,'Injetáveis','Moderno'),
            (4,'Diafragma / espuma / gel','Moderno'),(5,'Preservativo masculino','Moderno'),
            (6,'Esterilização feminina','Moderno'),(7,'Esterilização masculina','Moderno'),
            (8,'Abstinência periódica','Tradicional'),(9,'Coito interrompido','Tradicional')])
        for metodo in range(1,10):
            coluna=f'v304_{metodo:02d}'
            c.execute(f'''INSERT INTO Conhecimento_Metodo
            SELECT {mulher},?,{coluna} FROM fonte.Mulher
            WHERE {coluna} BETWEEN 0 AND 7''',(metodo,))
        # Pesquisas completas suplementares: entrevistas independentes, nunca imputadas
        # nas mulheres da pesquisa original. Uma pesquisa por país no tema contracepção.
        if len({s['pais_codigo'] for s in suplementos}) != len(suplementos):
            raise ValueError('Selecionar somente um suplemento por país.')
        for s in suplementos:
            import pyreadstat
            codigo, fase = s['pais_codigo'], s['fase']
            lev = codigo+'_'+fase
            colunas = ['v001','v002','v003','v024','v025','v190','v012','v106','v201','v212',
                       'v006','v007','v008','v005','v312']+[f'v304_{i:02d}' for i in range(1,10)]
            df, _ = pyreadstat.read_dta(str(s['caminho_origem']), usecols=colunas, apply_value_formats=False)
            if len(df)!=s['N'] or set(colunas)-set(df.columns):
                raise ValueError(f'Arquivo suplementar incompatível: {lev}')
            if df[['v001','v002','v003']].isna().any().any():
                raise ValueError(f'Chaves ausentes: {lev}')
            df['levantamento_id']=lev
            # pandas converte NaN em NULL; a tabela intermediária é removida após a carga.
            df.to_sql('ir_suplementar',c,index=False,if_exists='replace')
            c.execute('INSERT OR IGNORE INTO Levantamento VALUES(?,?,?)',(lev,codigo,fase))
            c.execute("UPDATE Entrevista SET coorte='nucleo_exclusivo' WHERE substr(mulher_id,1,2)=?",(codigo,))
            c.execute(f'''INSERT INTO Domicilio SELECT {dom},levantamento_id,v001,v002,MAX(v024),
                       MAX(CASE WHEN v025 IN(1,2) THEN v025 END),
                       MAX(CASE WHEN v190 BETWEEN 1 AND 5 THEN v190 END),
                       NULL,NULL,NULL,'IR_completo'
                       FROM ir_suplementar GROUP BY levantamento_id,v001,v002''')
            c.execute(f'''INSERT INTO Mulher SELECT {mulher},{dom},v003,v012,
                       CASE WHEN v106 BETWEEN 0 AND 3 THEN v106 END,v201,
                       CASE WHEN v212 BETWEEN 10 AND 49 THEN v212 END FROM ir_suplementar''')
            c.execute(f'''INSERT INTO Entrevista SELECT {mulher},CASE WHEN v007 BETWEEN 0 AND 99 THEN
                       CASE WHEN v008>0 THEN 1900+CAST((v008-1)/12 AS INTEGER) END ELSE v007 END,v006,v008,
                       CASE WHEN v005>0 THEN v005/1000000.0 END,
                       CASE WHEN v312=0 THEN 0 WHEN v312 BETWEEN 1 AND 19 THEN 1 END,
                       'contracepcao' FROM ir_suplementar''')
            for metodo in range(1,10):
                coluna=f'v304_{metodo:02d}'
                c.execute(f'''INSERT INTO Conhecimento_Metodo SELECT {mulher},?,{coluna}
                           FROM ir_suplementar WHERE {coluna} BETWEEN 0 AND 7''',(metodo,))
            c.execute('DROP TABLE ir_suplementar')
        # Índices de FK: integridade e navegação, além das PK/UNIQUE já existentes.
        c.executescript('''
        CREATE INDEX idx_dom_levantamento ON Domicilio(levantamento_id);
        CREATE INDEX idx_lev_pais ON Levantamento(pais_codigo);
        ''')
        falhas=c.execute('PRAGMA foreign_key_check').fetchall()
        if falhas: raise ValueError(f'Integridade referencial inválida: {falhas[:5]}')
        for tabela in ['Mulher','Crianca','Morador']:
            campo='COUNT(*)'
            bruto=c.execute(f'SELECT {campo} FROM fonte.{tabela}').fetchone()[0]
            final=c.execute(f'SELECT {campo} FROM {tabela}').fetchone()[0]
            if tabela=='Mulher':
                final=c.execute("SELECT COUNT(*) FROM Entrevista WHERE coorte!='contracepcao'").fetchone()[0]
            if bruto != final: raise ValueError(f'Perda de registros em {tabela}: {bruto} -> {final}')
        br=c.execute('SELECT COUNT(*) FROM fonte.Nascimento').fetchone()[0]
        if c.execute("SELECT COUNT(*) FROM Nascimento WHERE origem='BR'").fetchone()[0] != br:
            raise ValueError('Perda ou duplicidade de nascimentos BR.')
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise ValueError('Banco não passou na verificação de integridade.')
        c.commit()
    except Exception:
        c.close()
        temporario.unlink(missing_ok=True)
        raise
    c.close()
    os.replace(temporario,destino)
    return destino
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, Markdown, HTML
from time import perf_counter
from statistics import median
import hashlib


def sha256(arquivo):
    h=hashlib.sha256()
    with arquivo.open('rb') as f:
        for bloco in iter(lambda: f.read(4*1024*1024), b''): h.update(bloco)
    return h.hexdigest()

def abrir_banco(raiz, destino=None):
    """Reutiliza o banco preparado; reconstrói apenas quando o destino não existe."""
    raiz = Path(raiz).resolve()
    origem = raiz / "saude_mulher_dhs.db"
    destino = Path(destino or os.environ.get("DHS_REPORT_DB", raiz / "saude_mulher_normalizado.db")).resolve()
    if origem == destino:
        raise ValueError("Origem e destino devem ser diferentes.")
    hash_origem = sha256(origem)
    if not destino.exists():
        import json
        manifesto = json.loads((raiz / "docs/manifesto_contracepcao.json").read_text(encoding="utf-8"))
        pastas = [raiz / "dados/completo/extraidos", raiz / "dados/extraidos",
                  raiz.parent / "_dados_descartados_saude_mulher/completo/extraidos"]
        suplementos = []
        for item in manifesto:
            encontrados = [a for pasta in pastas if pasta.exists()
                           for a in pasta.rglob(item["arquivo_origem"])]
            if not encontrados:
                raise FileNotFoundError(f"Obter/extrair o arquivo DHS do manifesto: {item['arquivo_origem']}")
            suplementos.append(dict(item, caminho_origem=str(encontrados[0])))
        construir_banco(origem, destino, suplementos)
    conn = sqlite3.connect(destino)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Banco com vínculos inválidos; refaça a preparação.")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Banco não passou na verificação de integridade.")
        assert sha256(origem) == hash_origem, "A origem deve permanecer intacta."
    except Exception:
        conn.close()
        raise
    return conn, origem, hash_origem

# Apresentação: SQL visível, detalhes sob demanda e resultados em gráficos.
import html
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'figure.dpi':115})
AZUL, LARANJA = '#16758b', '#bc651b'

def detalhes(tabela, titulo='Resultado completo'):
    display(HTML('<details><summary>'+html.escape(titulo)+f' · {len(tabela):,} linhas</summary>'
                 +tabela.to_html(index=False,escape=True)+'</details>'))

def consultar(conn, sql, amostra=False):
    tabela=pd.read_sql_query(sql,conn)
    if amostra:
        detalhes(tabela.groupby('pais_codigo').head(1), 'Exemplo de cada país presente')
        # Evitar incorporar dezenas de milhares de microdados na saída do relatório.
        detalhes(tabela.groupby('pais_codigo').size().rename('registros').reset_index(), 'Contagens da seleção por país')
        display(Markdown(f'**Resultado:** {len(tabela):,} registros. Dados integrais em `r1`/`r2` após execução.'))
    else:
        detalhes(tabela)
    return tabela

def mostrar(fig):
    fig.tight_layout(); display(fig); plt.close(fig)

def barras(valores, titulo, unidade, percentual=False):
    valores=valores.dropna().sort_values()
    fig,ax=plt.subplots(figsize=(10,max(3,len(valores)*.23)))
    ax.barh(valores.index.astype(str),valores.values,color=AZUL)
    ax.set(title=titulo,xlabel=unidade,xlim=(0,100) if percentual else (0,None))
    ax.grid(axis='x',alpha=.15); mostrar(fig)

def mapa(tabela, titulo, unidade='%'):
    fig,ax=plt.subplots(figsize=(9,max(4,len(tabela)*.23)))
    cmap=plt.get_cmap('cividis').copy(); cmap.set_bad('#dddddd')
    im=ax.imshow(tabela.to_numpy(dtype=float),aspect='auto',cmap=cmap,vmin=0,vmax=100)
    ax.set(yticks=np.arange(len(tabela)),yticklabels=tabela.index,
           xticks=np.arange(len(tabela.columns)),xticklabels=tabela.columns,title=titulo)
    ax.tick_params(axis='x',labelrotation=25)
    for y,row in enumerate(tabela.to_numpy(dtype=float)):
        for x,v in enumerate(row):
            ax.text(x,y,'—' if np.isnan(v) else f'{v:.0f}',ha='center',va='center',fontsize=7,
                    color='white' if not np.isnan(v) and v<45 else 'black')
    fig.colorbar(im,ax=ax,label=unidade); mostrar(fig)

def pares(tabela, esquerda, direita, titulo, unidade='%'):
    tabela=tabela[[esquerda,direita]].dropna().sort_values(direita)
    fig,ax=plt.subplots(figsize=(10,max(4,len(tabela)*.23)))
    y=np.arange(len(tabela)); ax.hlines(y,tabela[esquerda],tabela[direita],color='#a0b0bc')
    ax.scatter(tabela[esquerda],y,label=esquerda,color=AZUL,marker='o')
    ax.scatter(tabela[direita],y,label=direita,color=LARANJA,marker='s')
    ax.set(yticks=y,yticklabels=tabela.index,title=titulo,xlabel=unidade,xlim=(0,100))
    ax.legend(loc='best'); ax.grid(axis='x',alpha=.15); mostrar(fig)



def comparar_residencias(r9, cobertura):
    ajustes=[]
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
    detalhes(ajustes.round(2), 'Padronização e cobertura do suporte comum')
    ausentes=sorted(set(cobertura.codigo)-set(ajustes.codigo))
    print('Países sem suporte comum suficiente:', ', '.join(ausentes) or 'nenhum')
    fig,ax=plt.subplots(figsize=(11,max(7,len(ajustes)*.28)))
    y=np.arange(len(ajustes))
    ax.hlines(y,ajustes.bruta_pp,ajustes.padronizada_pp,color='#a0b0bc')
    ax.scatter(ajustes.bruta_pp,y,label='Bruta no suporte comum',color='#aa687c')
    ax.scatter(ajustes.padronizada_pp,y,label='Padronizada: riqueza e escolaridade',color='#1a7a8c',marker='s')
    ax.set_yticks(y,ajustes.pais); ax.axvline(0,color='gray',lw=.7)
    ax.set_xlabel('Uso urbano − rural (pontos percentuais)'); ax.set_title('Quanto muda a diferença territorial ao padronizar riqueza e escolaridade?')
    ax.legend(loc='best'); ax.grid(axis='x',alpha=.2); fig.tight_layout(); display(fig); plt.close(fig)
    inversoes=ajustes[ajustes.inversao]
    maiores=ajustes.assign(mudanca=(ajustes.bruta_pp-ajustes.padronizada_pp).abs()).nlargest(3,'mudanca')
    display(Markdown(f"**Resultado:** {len(ajustes)} países com suporte comum; uso urbano maior após o ajuste em {int((ajustes.padronizada_pp > 0).sum())}; {len(inversoes)} inversões de sinal. Maiores mudanças: {', '.join(maiores.pais)}."))
    return ajustes


def verificar_sensibilidade(r9):
    # Sensibilidade: verificar inversões com mais respostas por estrato.
    sensibilidade=[]
    for minimo in [30,50,100]:
        for (codigo,nome),g in r9.groupby(['codigo','nome']):
            numeros=g.pivot(index=['riqueza','escolaridade'],columns='residencia',values='n')
            suporte=numeros.index[(numeros.get(1,0)>=minimo)&(numeros.get(2,0)>=minimo)]
            if len(suporte)==0: continue
            sub=g.set_index(['riqueza','escolaridade']).loc[suporte].reset_index()
            wt=sub.pivot(index=['riqueza','escolaridade'],columns='residencia',values='peso_total')
            uso=sub.pivot(index=['riqueza','escolaridade'],columns='residencia',values='peso_uso')
            padrao=(wt[1]+wt[2]); padrao=padrao/padrao.sum()
            bruta=100*(uso[1].sum()/wt[1].sum()-uso[2].sum()/wt[2].sum())
            ajustada=100*((uso[1]/wt[1]-uso[2]/wt[2])*padrao).sum()
            sensibilidade.append([codigo,nome,minimo,len(suporte),bruta,ajustada,bruta*ajustada<0])
    sensibilidade=pd.DataFrame(sensibilidade,columns=['codigo','pais','minimo_por_area','estratos','bruta_pp','padronizada_pp','inversao'])
    robustez=sensibilidade.groupby('minimo_por_area').agg(paises=('codigo','nunique'),inversoes=('inversao','sum'))
    fig,ax=plt.subplots(figsize=(7,3)); robustez.plot.bar(ax=ax,color=[AZUL,LARANJA],rot=0)
    ax.set(xlabel='Mínimo de respostas por área/estrato',ylabel='Países',title='Sensibilidade do suporte comum'); mostrar(fig)
    detalhes(sensibilidade.round(2), 'Sensibilidade por país e limiar')
    persistentes=sensibilidade.groupby('pais').filter(lambda g: len(g)==3 and g.inversao.all()).pais.unique()
    display(Markdown('**Sensibilidade:** inversão nos três limiares em ' + (', '.join(sorted(persistentes)) or 'nenhum país') + '. Os estratos incluídos mudam com o limiar.'))
    return sensibilidade


def comparar_prenatal(r10, cobertura):
    # Gradiente de pré-natal por país e riqueza, sem misturar pesos de países diferentes.
    prenatal=r10.groupby(['codigo','nome','riqueza'],as_index=False)[['nascimentos_recentes','n_validos','peso_valido','peso_quatro_mais']].sum()
    prenatal['percentual']=100*prenatal.peso_quatro_mais/prenatal.peso_valido.replace(0,np.nan)
    prenatal['cobertura_pct']=100*prenatal.n_validos/prenatal.nascimentos_recentes
    # Transparência: células com menos de 30 respostas não são comparadas no mapa.
    prenatal.loc[prenatal.n_validos<30,'percentual']=np.nan
    matriz=prenatal.pivot(index='nome',columns='riqueza',values='percentual').reindex(cobertura.nome.drop_duplicates().sort_values())
    assert matriz.index.is_unique and len(matriz)==cobertura.codigo.nunique()
    fig,ax=plt.subplots(figsize=(9,12))
    cmap=plt.get_cmap('cividis').copy(); cmap.set_bad('#dddddd')
    im=ax.imshow(matriz.to_numpy(),vmin=0,vmax=100,cmap=cmap,aspect='auto')
    ax.set_yticks(np.arange(len(matriz)),matriz.index); ax.set_xticks(np.arange(5),['Mais pobre','2','3','4','Mais rico'])
    for row in range(len(matriz)):
        for col in range(5):
            value=matriz.iloc[row,col]
            if pd.notna(value): ax.text(col,row,f'{value:.0f}',ha='center',va='center',fontsize=7,color='white' if value<45 else 'black')
    ax.set_title('Pré-natal ≥4 consultas: todos os países, por quintil de riqueza\nÚltimo nascimento recente; cinza = informação insuficiente')
    fig.colorbar(im,ax=ax,label='% ponderado entre respostas válidas'); fig.tight_layout(); display(fig); plt.close(fig)
    gradiente=matriz[[1,5]].dropna().copy(); gradiente['diferenca_pp']=gradiente[5]-gradiente[1]
    display(HTML('<details><summary>Gradiente entre quintis extremos</summary>'+gradiente.reset_index().round(2).to_html(index=False)+'</details>')) if 'HTML' in globals() else None
    coverage=prenatal.groupby('nome')[['n_validos','nascimentos_recentes']].sum()
    coverage['cobertura_pct']=100*coverage.n_validos/coverage.nascimentos_recentes
    display(HTML('<details><summary>Completude do pré-natal</summary>'+coverage.reset_index().round(2).to_html(index=False)+'</details>')) if 'HTML' in globals() else None
    display(Markdown(f"**Resultado:** pré-natal ≥4 maior no quintil mais rico em {int((gradiente.diferenca_pp > 0).sum())} de {len(gradiente)} países com respostas suficientes; diferença de {gradiente.diferenca_pp.min():.1f} a {gradiente.diferenca_pp.max():.1f} pontos percentuais."))
    return prenatal


def medir_otimizacao(conn):
    conn.execute('DROP INDEX IF EXISTS idx_entrevista_ano_uso')
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
    display(Markdown('```sql\n'+sql_otimizacao.strip()+'\n```'))
    display(Markdown('```sql\nCREATE INDEX idx_entrevista_ano_uso ON Entrevista(ano,usa_metodo,mulher_id,peso);\n```'))
    detalhes(plano_antes, f'Plano antes · ano {ano}')
    detalhes(plano_depois,'Plano depois')
    display(Markdown('**Plano:** '+plano_antes.detail.iloc[0]+' → '+plano_depois.detail.iloc[0]))
    detalhes(pd.DataFrame({'execucao':range(1,8),'antes_ms':np.array(tempos_antes)*1000,'depois_ms':np.array(tempos_depois)*1000}), 'Sete medições completas')
    med_antes,med_depois=median(tempos_antes),median(tempos_depois)
    ganho=100*(1-med_depois/med_antes)
    fig,ax=plt.subplots(figsize=(7,3))
    valores=[med_antes*1000,med_depois*1000]; ax.barh(['Antes','Depois'],valores,color=[LARANJA,AZUL])
    for y,v in enumerate(valores): ax.text(v,y,f' {v:.1f} ms',va='center')
    ax.set(xlim=(0,max(valores)*1.25),xlabel='Mediana de sete execuções completas (ms)',title=f'Índice de cobertura · ano {ano} · resultados equivalentes'); mostrar(fig)
    display(Markdown(f"**Resultado:** {med_antes*1000:.2f} → {med_depois*1000:.2f} ms; redução de {ganho:.1f}%. Criação do índice: {custo_indice:.2f} s. Resultados equivalentes; ganho específico deste filtro."))
    conn.execute('ANALYZE'); conn.commit()
    print('Banco derivado final com índice e estatísticas; resultados equivalentes confirmados.')
