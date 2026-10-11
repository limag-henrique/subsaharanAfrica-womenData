import json
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pipeline():
    nb = json.loads((ROOT / 'tp_template.ipynb').read_text(encoding='utf-8'))
    sources = [''.join(c['source']) for c in nb['cells']
               if 'pipeline_normalizado' in c.get('metadata', {}).get('tags', [])]
    if not sources:
        raise AssertionError('Notebook deve implementar a carga normalizada reproduzível.')
    namespace = {}
    exec('\n'.join(sources), namespace)
    return namespace['construir_banco']


def fixture(path):
    c = sqlite3.connect(path)
    c.executescript('''
    CREATE TABLE Pais(pais_codigo TEXT, nome_pais TEXT);
    INSERT INTO Pais VALUES ('AO','Angola'),('KM','Comores');
    CREATE TABLE Levantamento(levantamento_id TEXT,pais_codigo TEXT,fase TEXT);
    INSERT INTO Levantamento VALUES ('AO_81','AO','81'),('KM_61','KM','61');
    CREATE TABLE Domicilio(levantamento_id TEXT,hv001 INT,hv002 INT,hv024 INT,hv025 INT,hv270 INT,hv206 INT,hv201 INT,hv009 INT);
    INSERT INTO Domicilio VALUES ('AO_81',1,1,1,2,1,0,42,5);
    CREATE TABLE Mulher(levantamento_id TEXT,v001 INT,v002 INT,v003 INT,caseid TEXT,
    v024 INT,v025 INT,v190 INT,v012 INT,v106 INT,v201 INT,v212 INT,v006 INT,v007 INT,v008 INT,v005 INT,v312 INT,
    v304_01 INT,v304_02 INT,v304_03 INT,v304_04 INT,v304_05 INT,v304_06 INT,v304_07 INT,v304_08 INT,v304_09 INT);
    INSERT INTO Mulher VALUES ('AO_81',1,1,1,'  1 1 1',1,2,1,24,0,2,18,6,2023,1482,1000000,3,1,0,NULL,NULL,2,NULL,NULL,NULL,NULL);
    INSERT INTO Mulher VALUES ('KM_61',1,1,1,'         1 1 1',1,1,3,30,2,1,25,6,2013,1362,2000000,0,2,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
    CREATE TABLE Nascimento(levantamento_id TEXT,v001 INT,v002 INT,v003 INT,caseid TEXT,bidx INT,b1 INT,b2 INT,b3 INT,b4 INT,b5 INT,m14 INT,m15 INT,m17 INT,m3a INT,m3b INT);
    INSERT INTO Nascimento VALUES ('AO_81',1,1,1,'1 1 1',1,6,2022,1470,2,1,6,21,0,0,1);
    INSERT INTO Nascimento VALUES ('KM_61',1,1,1,'1 1 1',1,6,2012,1350,1,1,98,11,0,0,0);
    CREATE TABLE Crianca(levantamento_id TEXT,v001 INT,v002 INT,v003 INT,caseid TEXT,bidx INT,b1 INT,b2 INT,b3 INT,b4 INT,b5 INT,m14 INT,m15 INT,m17 INT,b8 INT,h11 INT,h1 INT);
    INSERT INTO Crianca VALUES ('AO_81',1,1,1,'1 1 1',1,6,2022,1470,2,1,6,21,0,1,0,1);
    INSERT INTO Crianca VALUES ('AO_81',1,1,1,'1 1 1',2,6,2021,1458,1,1,4,21,0,2,2,1);
    CREATE TABLE Morador(levantamento_id TEXT,hv001 INT,hv002 INT,hvidx INT,hv104 INT,hv105 INT,hv106 INT,hv101 INT);
    INSERT INTO Morador VALUES ('AO_81',1,1,1,2,24,0,1);
    ''')
    c.commit(); c.close()


class NotebookNormalizadoTest(unittest.TestCase):
    def test_carga_preserva_paises_e_conhecimento_sem_confundir_caseid(self):
        with tempfile.TemporaryDirectory() as directory:
            origem = Path(directory) / 'origem.db'
            destino = Path(directory) / 'normalizado.db'
            fixture(origem)
            pipeline()(origem, destino)
            with closing(sqlite3.connect(destino)) as c:
                self.assertEqual(c.execute('SELECT COUNT(*) FROM Pais').fetchone()[0], 2)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM Mulher').fetchone()[0], 2)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM Nascimento').fetchone()[0], 3)
                self.assertEqual(c.execute('SELECT COUNT(*) FROM Conhecimento_Metodo WHERE nivel > 0').fetchone()[0], 3)
                self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(c.execute("SELECT COUNT(*) FROM Domicilio WHERE origem='IR_sem_HR'").fetchone()[0], 1)

    def test_falha_referencial_preserva_origem_e_resultado_anterior(self):
        with tempfile.TemporaryDirectory() as directory:
            origem = Path(directory) / 'origem.db'
            destino = Path(directory) / 'normalizado.db'
            fixture(origem)
            destino.write_bytes(b'resultado anterior')
            with closing(sqlite3.connect(origem)) as c:
                c.execute('UPDATE Nascimento SET v003=99 WHERE levantamento_id=?', ('KM_61',))
                c.commit()
            anterior = origem.read_bytes()
            with self.assertRaises(sqlite3.IntegrityError):
                pipeline()(origem, destino)
            self.assertEqual(origem.read_bytes(), anterior)
            self.assertEqual(destino.read_bytes(), b'resultado anterior')

    def test_rejeita_duplicidade_da_entidade_em_vez_de_perder_registros(self):
        with tempfile.TemporaryDirectory() as directory:
            origem = Path(directory) / 'origem.db'
            destino = Path(directory) / 'normalizado.db'
            fixture(origem)
            with closing(sqlite3.connect(origem)) as c:
                c.execute("INSERT INTO Mulher SELECT * FROM Mulher WHERE levantamento_id='KM_61'")
                c.commit()
            with self.assertRaises(sqlite3.IntegrityError):
                pipeline()(origem, destino)
            self.assertFalse(destino.exists())


if __name__ == '__main__':
    unittest.main()
