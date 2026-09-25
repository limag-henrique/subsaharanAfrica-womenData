import os
import sys
import unittest
import sqlite3

# Ensure database_python is importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "database_python"))

import label_maps as lm
from server import app, DB_PATH


class FlaskEntitiesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.conn = sqlite3.connect(DB_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_all_database_columns_have_portuguese_labels(self):
        """Test that 100% of columns across all DB tables have readable labels."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]

        for table in tables:
            cursor.execute(f'PRAGMA table_info("{table}")')
            cols = [r[1] for r in cursor.fetchall()]
            for col in cols:
                label = lm.get_column_label(table, col)
                self.assertIsNotNone(label, f"Label is None for {table}.{col}")
                self.assertNotEqual(
                    label, col,
                    f"Column '{col}' in table '{table}' is still untranslated / in code!"
                )

    def test_servico_comunidade_specific_labels(self):
        """Test specific key columns of Servico_Comunidade are translated correctly."""
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "sqprov"), "Numero da Provincia")
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "sqdepart"), "Numero do Departamento")
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "sqgrappe"), "Numero do Cluster")
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "sqnom"), "Nome da Cidade / Bairro / Aldeia")
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "sqnbhab"), "Numero de Habitantes da Localidade")
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "sq111"), "Presenca de Rede Eletrica na Localidade")
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "urbrur"), "Area (1=Urbano, 2=Rural)")
        self.assertEqual(lm.get_column_label("Servico_Comunidade", "id_servico"), "ID do Servico Comunitario")

    def test_nascimento_b17_bugfix(self):
        """Test that b17 is Day of Birth, NOT Cesarean section."""
        label = lm.get_column_label("Nascimento", "b17")
        self.assertEqual(label, "Dia do Nascimento")
        self.assertNotIn("b17", lm.VALUE_MAPS)
        # Verify caesarean is m17
        self.assertEqual(lm.get_column_label("Nascimento", "m17"), "Parto Cesarea")
        self.assertEqual(lm.get_value_label("m17", 1), "Sim")
        self.assertEqual(lm.get_value_label("m17", 0), "Nao")

    def test_value_labels_robustness(self):
        """Test that get_value_label handles integers, strings, floats, and new maps."""
        # v025 Urban/Rural
        self.assertEqual(lm.get_value_label("v025", 1), "Urbano")
        self.assertEqual(lm.get_value_label("v025", "1"), "Urbano")
        self.assertEqual(lm.get_value_label("v025", 1.0), "Urbano")
        self.assertEqual(lm.get_value_label("v025", 2), "Rural")

        # urbrur and curbrur in Servico_Comunidade
        self.assertEqual(lm.get_value_label("urbrur", 1), "Urbano")
        self.assertEqual(lm.get_value_label("urbrur", "2"), "Rural")
        self.assertEqual(lm.get_value_label("curbrur", 1), "Urbano")

        # Anemia v457
        self.assertEqual(lm.get_value_label("v457", 1), "Anemia severa")
        self.assertEqual(lm.get_value_label("v457", 4), "Nao anemica")

        # Antropometria hwlevel
        self.assertEqual(lm.get_value_label("hwlevel", 1), "Domicilio")
        self.assertEqual(lm.get_value_label("hwlevel", 2), "Individual")

        # Contraceptive knowledge v304
        self.assertEqual(lm.get_value_label("v304_01", 1), "Conhece")
        self.assertEqual(lm.get_value_label("v304_01", 0), "Nao conhece")

    def test_api_tables(self):
        """Test /api/tables endpoint returns all tables with positive counts."""
        resp = self.client.get("/api/tables")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        table_names = {t["name"] for t in data}
        self.assertIn("Servico_Comunidade", table_names)
        self.assertIn("Mulher", table_names)
        self.assertIn("Antropometria", table_names)
        self.assertIn("Casal", table_names)

        sq_info = next(t for t in data if t["name"] == "Servico_Comunidade")
        self.assertEqual(sq_info["count"], 5154)

    def test_api_columns_servico_comunidade(self):
        """Test /api/columns for Servico_Comunidade returns all labeled columns."""
        resp = self.client.get("/api/columns?table=Servico_Comunidade")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data), 804)
        for col_info in data:
            self.assertNotEqual(col_info["label"], col_info["code"])

    def test_api_data_servico_comunidade(self):
        """Test /api/data for Servico_Comunidade paginated data."""
        resp = self.client.get("/api/data?table=Servico_Comunidade&page=1&per_page=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 5154)
        self.assertEqual(len(data["rows"]), 5)
        self.assertIn("column_labels", data)
        self.assertEqual(data["column_labels"]["sqprov"], "Numero da Provincia")

    def test_api_data_antropometria(self):
        """Test /api/data for Antropometria."""
        resp = self.client.get("/api/data?table=Antropometria&page=1&per_page=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["total"], 150700)
        self.assertEqual(len(data["rows"]), 5)
        self.assertEqual(data["column_labels"]["hc70"], "Altura/Idade em Desvios-Padrao (OMS)")


if __name__ == "__main__":
    unittest.main()
