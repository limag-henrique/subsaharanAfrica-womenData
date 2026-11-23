"""Regressões na interface pública de preparação do banco final."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
from contextlib import closing

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class DatasEIdentidade(unittest.TestCase):
    def test_reconstrucao_respeita_colunas_do_ddl_do_notebook(self):
        from database_python.partos import migrar_banco_partos, DDL_PARTOS
        from database_python.relatorio_notebook import DDL_NORMALIZADO
        with tempfile.TemporaryDirectory() as pasta:
            legado, bruto, destino = (Path(pasta)/n for n in ('legado.db','bruto.db','partos.db'))
            with closing(sqlite3.connect(legado)) as c:
                c.executescript(DDL_NORMALIZADO)
                c.executescript('''
                    INSERT INTO Pais VALUES ('AO','Angola');
                    INSERT INTO Levantamento VALUES ('AO_81','AO','81');
                    INSERT INTO Domicilio(id,levantamento_id,cluster,numero,origem)
                        VALUES ('AO_81|1|1','AO_81',1,1,'HR');
                    INSERT INTO Mulher(id,domicilio_id,linha) VALUES ('AO_81|1|1|1','AO_81|1|1',1);
                    INSERT INTO Nascimento(id,mulher_id,indice,ano,mes,data_cmc,sexo,vivo,origem)
                        VALUES ('AO_81|1|1|1|1','AO_81|1|1|1',1,2020,1,1441,1,1,'BR');
                    INSERT INTO Crianca VALUES ('AO_81|1|1|1|1',1,0,1);
                    INSERT INTO Vacina_Remedio VALUES (1,'h2','BCG');
                    INSERT INTO Crianca_Vacina VALUES ('AO_81|1|1|1|1',1,1);
                ''')
            with closing(sqlite3.connect(bruto)) as c:
                c.executescript('''
                    CREATE TABLE Nascimento(levantamento_id,v001,v002,v003,bidx,b0);
                    CREATE TABLE Crianca(levantamento_id,v001,v002,v003,bidx,b0);
                    INSERT INTO Nascimento VALUES ('AO_81',1,1,1,1,0);
                ''')
            ddl = DDL_PARTOS.replace('  diarreia_codigo INTEGER, cartao_vacina_codigo INTEGER,\n','')
            migrar_banco_partos(legado,bruto,destino,ddl)
            with closing(sqlite3.connect(destino)) as c:
                self.assertEqual(c.execute('SELECT id,idade_anos FROM Crianca').fetchall(),[('AO_81|1|1|1|1',1)])
                self.assertEqual(c.execute('SELECT COUNT(*) FROM Crianca_Vacina').fetchone()[0],1)

    def test_datas_derivadas_preservam_identidade_e_fontes(self):
        from database_python.normalizacao_final import normalizar_datas
        with tempfile.TemporaryDirectory() as pasta:
            origem, destino = (Path(pasta) / n for n in ('fonte.db', 'final.db'))
            with closing(sqlite3.connect(origem)) as c:
                c.executescript('''
                    CREATE TABLE Mulher(id TEXT PRIMARY KEY, domicilio_id TEXT, linha INTEGER,
                        UNIQUE(domicilio_id,linha));
                    CREATE TABLE Entrevista(mulher_id TEXT PRIMARY KEY REFERENCES Mulher(id),
                        ano INTEGER,mes INTEGER,data_cmc INTEGER);
                    CREATE TABLE Nascimento(id TEXT PRIMARY KEY,mulher_id TEXT REFERENCES Mulher(id),
                        ano INTEGER,mes INTEGER,data_cmc INTEGER);
                    INSERT INTO Mulher VALUES ('AO_81|1|1|1','AO_81|1|1',1),
                        ('AO_81|1|2|1','AO_81|1|2',1);
                    INSERT INTO Entrevista VALUES ('AO_81|1|1|1',2020,1,1441),
                        ('AO_81|1|2|1',2020,12,1452);
                    INSERT INTO Nascimento VALUES ('parto-a','AO_81|1|1|1',2019,12,1440);
                    CREATE INDEX idx_datas ON Entrevista(ano,mes);
                ''')
                c.commit()
            antes = origem.read_bytes()
            ddl = '''
                CREATE TABLE Mulher(id TEXT PRIMARY KEY, domicilio_id TEXT, linha INTEGER,
                    UNIQUE(domicilio_id,linha));
                CREATE TABLE Entrevista(mulher_id TEXT PRIMARY KEY REFERENCES Mulher(id),data_cmc INTEGER);
                CREATE TABLE Nascimento(id TEXT PRIMARY KEY,mulher_id TEXT REFERENCES Mulher(id),data_cmc INTEGER);
            '''
            normalizar_datas(origem, destino, ddl)
            with closing(sqlite3.connect(destino)) as c:
                self.assertEqual(c.execute('SELECT ano,mes FROM Entrevista_Analitica ORDER BY mulher_id').fetchall(),
                                 [(2020,1),(2020,12)])
                self.assertEqual(c.execute('SELECT ano,mes FROM Nascimento_Analitico').fetchall(),[(2019,12)])
                self.assertNotIn('ano',[r[1] for r in c.execute('PRAGMA table_info(Entrevista)')])
                self.assertEqual(c.execute('SELECT COUNT(*) FROM Mulher WHERE linha=1').fetchone()[0],2)
                self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
            self.assertEqual(origem.read_bytes(),antes)
            normalizar_datas(origem, destino, ddl)  # Reexecução idempotente.


if __name__ == '__main__':
    unittest.main()
