"""Regressão do recorte por ano da entrevista no esquema de datas canônicas."""
import ast
import json
import sqlite3
import unittest
from pathlib import Path


class RecorteEntrevistas(unittest.TestCase):
    def test_recorte_usa_datas_derivadas_e_inclui_limites(self):
        notebook = json.loads((Path(__file__).resolve().parents[1] /
            'Saúde da Mulher na África Subsaariana.ipynb').read_text(encoding='utf-8'))
        sql = None
        for cell in notebook['cells']:
            if cell['cell_type'] != 'code':
                continue
            for node in ast.parse(''.join(cell['source'])).body:
                if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == 'sql_1b' for t in node.targets):
                    sql = ast.literal_eval(node.value)
        self.assertIsNotNone(sql)
        with sqlite3.connect(':memory:') as conn:
            conn.executescript("""
                CREATE TABLE Entrevista(mulher_id TEXT PRIMARY KEY, data_cmc INTEGER);
                CREATE VIEW Entrevista_Analitica AS
                  SELECT *, 1900 + CAST((data_cmc-1)/12 AS INTEGER) AS ano FROM Entrevista;
                INSERT INTO Entrevista VALUES
                  ('XX_antiga',1381), ('XX_inicio',1393), ('XX_fim',1512), ('XX_futura',1513);
            """)
            rows = conn.execute(sql).fetchall()
        self.assertEqual(sorted(rows), [('XX', 'XX_fim', 2025), ('XX', 'XX_inicio', 2016)])


if __name__ == '__main__':
    unittest.main()
