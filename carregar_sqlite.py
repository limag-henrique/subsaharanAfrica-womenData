"""
Script utilitário para carregar datasets extraídos (.dta - Stata) para um banco de dados SQLite local.
Alinhado aos requisitos do trabalho prático de DCC011 (Introdução a Banco de Dados).
"""

import sqlite3
from pathlib import Path
import argparse
import pandas as pd


def load_dta_to_sqlite(dta_path: str, db_path: str = "saude_africa.db", table_name: str = None, if_exists: str = "replace"):
    dta_file = Path(dta_path)
    if not dta_file.exists():
        raise FileNotFoundError(f"Arquivo Stata (.dta) não encontrado: {dta_path}")

    if not table_name:
        table_name = dta_file.stem.lower()

    print(f"[SQLITE] Lendo arquivo Stata: {dta_file}...")
    # Leitura em chunks para evitar estourar memória em datasets grandes
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Dica da descrição do trabalho: acelerar inserção
    cursor.execute("PRAGMA foreign_keys = 0;")
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = MEMORY;")

    try:
        reader = pd.read_stata(dta_file, chunksize=20000, convert_categoricals=False)
        total_rows = 0
        first_chunk = True

        for chunk in reader:
            mode = if_exists if first_chunk else "append"
            chunk.to_sql(table_name, conn, if_exists=mode, index=False)
            total_rows += len(chunk)
            first_chunk = False
            print(f"  Inseridas {total_rows} linhas...")

        conn.commit()
        print(f"[SUCESSO] Tabela '{table_name}' criada com {total_rows} registros no banco '{db_path}'.")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Carrega arquivo .dta (Stata) no SQLite.")
    parser.add_argument("dta_path", help="Caminho do arquivo .dta extraído.")
    parser.add_argument("--db", default="saude_africa.db", help="Nome do arquivo SQLite.")
    parser.add_argument("--table", help="Nome da tabela no SQLite.")
    args = parser.parse_args()

    load_dta_to_sqlite(args.dta_path, db_path=args.db, table_name=args.table)


if __name__ == "__main__":
    main()
