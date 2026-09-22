import csv
import tempfile
import unittest
from pathlib import Path

from database_python.catalogo import load_catalog


class CatalogoTest(unittest.TestCase):
    def test_load_catalog_reads_exported_csv(self):
        row = {
            "filename": "AOIR81DT.zip",
            "country_code": "AO",
            "country_name": "Angola",
            "recode_code": "IR",
            "recode_name": "Mulheres (Individual Recode)",
            "recode_description": "Dados de mulheres",
            "category_folder": "Saude_da_Mulher_IR",
            "phase_version": "81",
            "format": "Stata (.dta)",
            "surv_id": "569",
            "url": "https://example.test/download?Filename=AOIR81DT.zip",
            "relative_path": "Angola/Saude_da_Mulher_IR/AOIR81DT.zip",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalogo.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=row.keys())
                writer.writeheader()
                writer.writerow(row)

            catalog = load_catalog(str(path))

        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]["filename"], "AOIR81DT.zip")
        self.assertEqual(catalog[0]["recode_code"], "IR")


if __name__ == "__main__":
    unittest.main()
