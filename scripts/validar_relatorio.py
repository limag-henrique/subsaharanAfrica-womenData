"""Verifica os denominadores das consultas usando dados pequenos e conhecidos."""
import ast
import json
import sqlite3
import unittest
from pathlib import Path
from contextlib import closing

RAIZ = Path(__file__).resolve().parents[1]
NOTEBOOK = RAIZ / 'Saúde da Mulher na África Subsaariana.ipynb'


def consultas():
    resultado = {}
    notebook = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    for celula in notebook['cells']:
        if celula['cell_type'] != 'code':
            continue
        for comando in ast.parse(''.join(celula['source'])).body:
            if isinstance(comando, ast.Assign) and isinstance(comando.value, ast.Constant):
                for alvo in comando.targets:
                    if isinstance(alvo, ast.Name) and alvo.id.startswith('sql_'):
                        resultado[alvo.id] = comando.value.value
    return resultado


class Denominadores(unittest.TestCase):
    def setUp(self):
        self.banco = sqlite3.connect(':memory:')
        self.banco.row_factory = sqlite3.Row
        self.banco.executescript('''
            CREATE TABLE Mulher(id, domicilio_id, linha, idade, escolaridade, filhos_nascidos_vivos);
            CREATE TABLE Entrevista(mulher_id, ano, usa_metodo, coorte);
            CREATE VIEW Entrevista_Analitica AS SELECT * FROM Entrevista;
            CREATE TABLE Domicilio(id, residencia, levantamento_id);
            CREATE TABLE Morador(domicilio_id, linha, relacao_chefe_codigo);
            CREATE TABLE Levantamento(id, pais_codigo);
            INSERT INTO Levantamento VALUES ('XX_1', 'XX');
            INSERT INTO Domicilio VALUES ('d', 1, 'XX_1');
            INSERT INTO Mulher VALUES ('a','d',1,20,2,2),('b','d',2,30,NULL,NULL),('c','d',3,40,2,4);
            INSERT INTO Entrevista VALUES
                ('a',2020,1,'contracepcao'),('b',2020,NULL,'contracepcao'),
                ('c',2020,NULL,'nucleo_exclusivo');
            INSERT INTO Morador VALUES ('d',1,1),('d',2,1),('d',3,1);
        ''')
        self.sql = consultas()

    def tearDown(self):
        self.banco.close()

    def test_contracepcao_conta_apenas_respostas_validas(self):
        linhas = [dict(r) for r in self.banco.execute(self.sql['sql_4'])]
        self.assertEqual(sum(r['total_entrevistas'] for r in linhas), 2)
        self.assertEqual(sum(r['respostas_validas'] for r in linhas), 1)
        self.assertEqual(sum(r['usuarias'] or 0 for r in linhas), 1)
        self.assertEqual(next(r['percentual_uso'] for r in linhas if r['respostas_validas']), 100)
        self.assertIsNone(next(r['percentual_uso'] for r in linhas if not r['respostas_validas']))

    def test_perfil_preserva_somas_e_bases_validas(self):
        r = dict(self.banco.execute(self.sql['sql_7']).fetchone())
        self.assertEqual(r['mulheres'], 3)
        self.assertEqual(r['n_filhos'], 2)
        self.assertEqual(r['soma_filhos'] / r['n_filhos'], 3)
        self.assertEqual(r['n_escolaridade'], 2)
        self.assertEqual(100 * r['secundario'] / r['n_escolaridade'], 100)
        self.assertEqual(r['soma_idade'] / r['n_idade'], 30)


class Modelos(unittest.TestCase):
    def test_diagrama_corresponde_ao_ddl(self):
        from gerar_diagramas import esquema
        import re
        with closing(esquema()) as banco:
            fonte = (RAIZ / 'docs/Diagrama Relacional.mmd').read_text(encoding='utf-8')
            for tabela, in banco.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                bloco = re.search(r'\b' + tabela + r' \{(.*?)\}', fonte, re.S).group(1)
                atributos = [(l.split()[1], l.split()[0]) for l in bloco.splitlines() if l.strip()]
                self.assertEqual(atributos, [(r[1],r[2]) for r in banco.execute(f'PRAGMA table_info({tabela})')])


class Conhecimento(unittest.TestCase):
    def test_codigo_sete_e_ausencias_nao_viram_desconhecimento(self):
        sql = consultas()['sql_10']
        # Executa o CTE real; 7 é conhecimento por uso atual, 8 não foi perguntado.
        trecho = sql.split('conhecimento AS (', 1)[1].split('),\ncontracepcao AS (', 1)[0]
        with closing(sqlite3.connect(':memory:')) as c:
            c.executescript('''
                CREATE TABLE Metodo(id INTEGER, classe TEXT);
                CREATE TABLE Conhecimento_Metodo(mulher_id TEXT, metodo_id INTEGER, nivel INTEGER);
                INSERT INTO Metodo VALUES (1,'Moderno'),(2,'Moderno'),(4,'Moderno');
                INSERT INTO Conhecimento_Metodo VALUES
                  ('uso',1,7),('uso',2,0),('nao',1,0),('nao',2,0),
                  ('ignorado',1,8),('ignorado',2,8),('parcial',1,0),('parcial',2,8),
                  ('ignorado',4,7),('parcial',4,7);
            ''')
            respostas = dict(c.execute(trecho))
            self.assertEqual(respostas['uso'], 1)
            self.assertEqual(respostas['nao'], 0)
            self.assertIsNone(respostas['ignorado'])
            self.assertIsNone(respostas['parcial'])


if __name__ == '__main__':
    unittest.main()
