from pathlib import Path
import os
import sqlite3


def construir_banco(origem, destino):
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
          origem TEXT NOT NULL CHECK(origem IN('HR','IR_sem_HR')),
          UNIQUE(levantamento_id,cluster,numero));
        CREATE TABLE Mulher(
          id TEXT PRIMARY KEY, domicilio_id TEXT NOT NULL REFERENCES Domicilio(id), linha INTEGER NOT NULL,
          idade INTEGER, escolaridade INTEGER CHECK(escolaridade BETWEEN 0 AND 3),
          filhos_nascidos_vivos INTEGER, idade_primeiro_nascimento INTEGER,
          UNIQUE(domicilio_id,linha));
        CREATE TABLE Entrevista(
          mulher_id TEXT PRIMARY KEY REFERENCES Mulher(id), ano INTEGER, mes INTEGER,
          data_cmc INTEGER, peso REAL CHECK(peso>0), usa_metodo INTEGER CHECK(usa_metodo IN(0,1)));
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
        SELECT {mulher},v007,v006,v008,
               CASE WHEN v005>0 THEN v005/1000000.0 END,
               CASE WHEN v312=0 THEN 0 WHEN v312 BETWEEN 1 AND 19 THEN 1 END
        FROM fonte.Mulher''')
        for tabela, origem_registro in [('Nascimento','BR'),('Crianca','KR_sem_BR')]:
            assistencia='m3a,m3b' if tabela=='Nascimento' else 'NULL,NULL'
            c.execute(f'''INSERT OR IGNORE INTO Nascimento
            SELECT {nasc},{mulher},bidx,b2,b1,b3,
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
