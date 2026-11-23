"""Publica o esquema final sem redundância de datas e sem alterar as fontes."""
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4


VIEWS_DATAS = '''
CREATE VIEW Entrevista_Analitica AS
SELECT *, 1900 + CAST((data_cmc - 1) / 12 AS INTEGER) AS ano,
          1 + ((data_cmc - 1) % 12) AS mes
FROM Entrevista;
CREATE VIEW Nascimento_Analitico AS
SELECT *, 1900 + CAST((data_cmc - 1) / 12 AS INTEGER) AS ano,
          1 + ((data_cmc - 1) % 12) AS mes
FROM Nascimento;
'''


def normalizar_datas(origem, destino, ddl):
    """Copia as relações para o DDL final, confere os dados e publica atomicamente.

    Ano e mês ficam disponíveis em views, calculados a partir do CMC do próprio
    arquivo DHS. O cálculo não converte calendários nacionais para gregoriano.
    """
    origem, destino = Path(origem).resolve(), Path(destino).resolve()
    if origem == destino:
        raise ValueError('Escolha um destino diferente da base de preparação.')
    with closing(sqlite3.connect(':memory:')) as esperado:
        esperado.executescript(ddl + VIEWS_DATAS)
        definicoes = dict(esperado.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('table','view')"))
    if destino.exists():
        with closing(sqlite3.connect(destino.as_uri() + '?mode=ro', uri=True)) as c:
            existentes = dict(c.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('table','view')"))
            if definicoes != existentes:
                raise ValueError('Banco final incompatível; escolha um destino novo.')
            if destino.stat().st_mtime_ns < origem.stat().st_mtime_ns:
                raise ValueError('A preparação mudou; escolha um destino novo para reconstruir.')
            if c.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Banco final com vínculos inválidos.')
        return destino
    temporario = destino.with_name(f'.final_{uuid4().hex}.db')
    try:
        with closing(sqlite3.connect(temporario.as_uri(), uri=True)) as c:
            c.execute('PRAGMA foreign_keys=ON')
            c.execute('ATTACH DATABASE ? AS fonte', (origem.as_uri() + '?mode=ro',))
            for tabela in ('Entrevista', 'Nascimento'):
                if c.execute(f'''SELECT 1 FROM fonte.{tabela}
                    WHERE data_cmc IS NULL OR data_cmc <= 0
                       OR ano IS NULL OR mes IS NULL
                       OR ano != 1900 + CAST((data_cmc-1)/12 AS INTEGER)
                       OR mes != 1 + ((data_cmc-1)%12) LIMIT 1''').fetchone():
                    raise ValueError(f'Datas não deriváveis sem perda em {tabela}.')
            c.executescript(ddl + VIEWS_DATAS)
            c.execute('BEGIN')
            tabelas = [r[0] for r in c.execute("SELECT name FROM main.sqlite_master WHERE type='table'")]
            for tabela in tabelas:
                colunas = ','.join('"'+r[1]+'"' for r in c.execute(f'PRAGMA main.table_info("{tabela}")'))
                c.execute(f'INSERT INTO main."{tabela}" ({colunas}) SELECT {colunas} FROM fonte."{tabela}"')
                if c.execute(f'SELECT {colunas} FROM fonte."{tabela}" EXCEPT SELECT {colunas} FROM main."{tabela}" LIMIT 1').fetchone():
                    raise ValueError(f'Dados alterados em {tabela}.')
                contagem = c.execute(f'SELECT (SELECT COUNT(*) FROM main."{tabela}") = (SELECT COUNT(*) FROM fonte."{tabela}")').fetchone()[0]
                if not contagem:
                    raise ValueError(f'Contagem diferente em {tabela}.')
            for tabela, sql in c.execute("SELECT tbl_name,sql FROM fonte.sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall():
                if tabela in ('Entrevista', 'Nascimento'):
                    sql = re.sub(r'\bano\b', '(1900 + CAST((data_cmc - 1) / 12 AS INTEGER))', sql)
                    sql = re.sub(r'\bmes\b', '(1 + ((data_cmc - 1) % 12))', sql)
                c.execute(sql)
            if c.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Integridade referencial inválida.')
            c.commit()
            if c.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Banco final sem integridade.')
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)
    return destino
