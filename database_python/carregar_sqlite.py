"""Carrega os recodes compactos do projeto em um banco SQLite relacional.

Os CSVs consolidados podem ter larguras diferentes por país: cada linha deve
ser interpretada com as colunas daquele país descritas no manifesto. O loader
usa o manifesto para alinhar essas linhas sem modificar os arquivos de origem.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import os
import sqlite3
from pathlib import Path


ENTITIES = {
    "IR": "Mulher",
    "BR": "Nascimento",
    "HR": "Domicilio",
    "PR": "Morador",
    "KR": "Crianca",
    "HW": "Antropometria",
    "CR": "Casal",
    "MR": "Parceiro",
    "SQ": "Servico_Comunidade",
    "WI": "Indice_Riqueza",
}

PREFIX_COLUMNS = [
    "pais_codigo", "pais_nome", "levantamento_id", "fase", "arquivo_origem", "linha_origem"
]
DERIVED_COLUMNS = {
    "IR": ["id_mulher", "id_domicilio", "id_mulher_global"],
    "BR": ["id_mulher", "id_domicilio", "id_nascimento"],
    "HR": ["id_domicilio"],
    "PR": ["id_domicilio", "id_morador"],
    "KR": ["id_mulher", "id_domicilio", "id_crianca"],
    "HW": ["id_medicao"],
    "CR": ["id_mulher", "id_domicilio", "id_casal"],
    "MR": ["id_parceiro"],
    "SQ": ["id_servico"],
    "WI": ["id_domicilio"],
}
TEXT_COLUMNS = {
    "pais_codigo", "pais_nome", "levantamento_id", "arquivo_origem", "fase",
    "caseid", "hhid", "mcaseid", "hwhhid", "whhid",
    *[name for names in DERIVED_COLUMNS.values() for name in names],
}
BATCH_SIZE = 10_000


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def manifest_rows(manifest: Path) -> list[dict[str, str]]:
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"pais_codigo", "pais_nome", "fase", "recode", "arquivo_origem", "linhas", "colunas"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Manifesto ausente ou incompleto: {manifest}")
    invalid = sorted({row["recode"] for row in rows} - ENTITIES.keys())
    if invalid:
        raise ValueError(f"Recodes sem entidade configurada: {', '.join(invalid)}")
    return rows


def columns_for(row: dict[str, str]) -> list[str]:
    source_columns = row["colunas"].split("|") if row["colunas"] else []
    columns = PREFIX_COLUMNS + source_columns + DERIVED_COLUMNS[row["recode"]]
    if len(columns) != len(set(columns)):
        raise ValueError(f"Colunas duplicadas no esquema de {row['recode']} / {row['pais_codigo']}")
    return columns


def schema_for(recode: str, rows: list[dict[str, str]]) -> list[str]:
    schema: list[str] = []
    for row in rows:
        if row["recode"] == recode:
            for column in columns_for(row):
                if column not in schema:
                    schema.append(column)
    return schema


def create_database(conn: sqlite3.Connection, rows: list[dict[str, str]]) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE Pais (
            pais_codigo TEXT PRIMARY KEY,
            nome_pais TEXT NOT NULL UNIQUE
        );
        CREATE TABLE Levantamento (
            levantamento_id TEXT PRIMARY KEY,
            pais_codigo TEXT NOT NULL REFERENCES Pais(pais_codigo),
            fase TEXT NOT NULL,
            UNIQUE (pais_codigo, fase)
        );
    """)

    countries: dict[str, str] = {}
    rounds: dict[str, tuple[str, str]] = {}
    for row in rows:
        country, name, phase = row["pais_codigo"], row["pais_nome"], row["fase"]
        if country in countries and countries[country] != name:
            raise ValueError(f"Nomes de país inconsistentes para {country}")
        countries[country] = name
        round_id = f"{country}_{phase}"
        if round_id in rounds and rounds[round_id] != (country, phase):
            raise ValueError(f"Levantamento inconsistente: {round_id}")
        rounds[round_id] = (country, phase)

    conn.executemany("INSERT INTO Pais VALUES (?, ?)", sorted(countries.items()))
    conn.executemany(
        "INSERT INTO Levantamento VALUES (?, ?, ?)",
        [(round_id, country, phase) for round_id, (country, phase) in sorted(rounds.items())],
    )

    for recode, table in ENTITIES.items():
        columns = schema_for(recode, rows)
        definitions = [
            f"{quote(column)} {'TEXT' if column in TEXT_COLUMNS else ('INTEGER' if column == 'linha_origem' else 'NUMERIC')}"
            for column in columns
        ]
        definitions.extend([
            f"FOREIGN KEY ({quote('pais_codigo')}) REFERENCES Pais(pais_codigo)",
            f"FOREIGN KEY ({quote('levantamento_id')}) REFERENCES Levantamento(levantamento_id)",
        ])
        conn.execute(f"CREATE TABLE {quote(table)} ({', '.join(definitions)})")

    manifest_columns = list(rows[0].keys())
    manifest_definitions = [
        f"{quote(column)} {'INTEGER' if column in {'linhas', 'colunas_selecionadas'} else 'TEXT'}"
        for column in manifest_columns
    ]
    manifest_definitions.append("PRIMARY KEY (pais_codigo, recode)")
    conn.execute(f"CREATE TABLE Manifesto_Selecao ({', '.join(manifest_definitions)})")


def read_manifesto_into_db(
    conn: sqlite3.Connection, manifest: Path, rows: list[dict[str, str]]
) -> None:
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        names = reader.fieldnames or []
        sql = f"INSERT INTO Manifesto_Selecao ({', '.join(map(quote, names))}) VALUES ({', '.join('?' for _ in names)})"
        conn.executemany(sql, ([row.get(name) for name in names] for row in reader))


def import_recode(conn: sqlite3.Connection, data_dir: Path, recode: str, rows: list[dict[str, str]]) -> int:
    source = data_dir / f"{recode}.csv.gz"
    if not source.is_file():
        raise FileNotFoundError(f"Arquivo de entidade não encontrado: {source}")
    table = ENTITIES[recode]
    expected_rows = [row for row in rows if row["recode"] == recode]
    total = 0

    with gzip.open(source, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"Arquivo vazio: {source}")
        first_schema = columns_for(expected_rows[0])
        if header != first_schema:
            raise ValueError(
                f"Cabeçalho de {source.name} não corresponde ao primeiro esquema do manifesto "
                f"({len(header)} colunas no arquivo, {len(first_schema)} esperadas)."
            )

        for manifest_row in expected_rows:
            source_columns = columns_for(manifest_row)
            insert_sql = (
                f"INSERT INTO {quote(table)} ({', '.join(map(quote, source_columns))}) "
                f"VALUES ({', '.join('?' for _ in source_columns)})"
            )
            remaining = int(manifest_row["linhas"])
            batch: list[list[str | None]] = []
            for _ in range(remaining):
                values = next(reader, None)
                if values is None:
                    raise ValueError(
                        f"{source.name} terminou antes de completar {manifest_row['pais_codigo']} "
                        f"({total} de {sum(int(r['linhas']) for r in expected_rows)} linhas lidas)."
                    )
                if len(values) != len(source_columns):
                    raise ValueError(
                        f"Linha de {source.name} para {manifest_row['pais_codigo']} tem "
                        f"{len(values)} valores; manifesto espera {len(source_columns)}."
                    )
                if values[:5] != [
                    manifest_row["pais_codigo"], manifest_row["pais_nome"],
                    f"{manifest_row['pais_codigo']}_{manifest_row['fase']}",
                    manifest_row["fase"], manifest_row["arquivo_origem"],
                ]:
                    raise ValueError(f"Metadados de linha não correspondem ao manifesto para {manifest_row['pais_codigo']}")
                batch.append([None if value == "" else value for value in values])
                if len(batch) >= BATCH_SIZE:
                    conn.executemany(insert_sql, batch)
                    total += len(batch)
                    batch.clear()
            if batch:
                conn.executemany(insert_sql, batch)
                total += len(batch)

        if next(reader, None) is not None:
            raise ValueError(f"{source.name} contém linhas além das contagens do manifesto")

    return total


def create_indexes(conn: sqlite3.Connection) -> None:
    for table in ENTITIES.values():
        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({quote(table)})")}
        for column in ("pais_codigo", "levantamento_id", "id_mulher_global", "id_mulher", "id_domicilio", "id_nascimento", "id_crianca", "id_morador"):
            if column in columns:
                conn.execute(
                    f"CREATE INDEX {quote('idx_' + table.lower() + '_' + column)} "
                    f"ON {quote(table)} ({quote(column)})"
                )


def load_project_data(data_dir: Path, db_path: Path) -> dict[str, int]:
    manifest = data_dir / "manifesto_selecao.csv"
    rows = manifest_rows(manifest)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = db_path.with_name(db_path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()

    counts: dict[str, int] = {}
    conn = sqlite3.connect(temporary)
    try:
        conn.execute("PRAGMA journal_mode = OFF")
        conn.execute("PRAGMA synchronous = OFF")
        create_database(conn, rows)
        read_manifesto_into_db(conn, manifest, rows)
        for recode in ENTITIES:
            counts[recode] = import_recode(conn, data_dir, recode, rows)
            print(f"{ENTITIES[recode]} ({recode}): {counts[recode]:,} linhas")
        create_indexes(conn)
        violations = list(conn.execute("PRAGMA foreign_key_check"))
        if violations:
            raise ValueError(f"Chaves estrangeiras inválidas: {violations[:5]}")
        conn.commit()
    except Exception:
        conn.close()
        if temporary.exists():
            temporary.unlink()
        raise
    else:
        conn.close()

    os.replace(temporary, db_path)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Carrega as entidades DHS compactas em um banco SQLite.")
    parser.add_argument("--data-dir", type=Path, default=Path("dados/relevantes"), help="Pasta com os CSVs gzip e o manifesto.")
    parser.add_argument("--db", type=Path, default=Path("saude_mulher_dhs.db"), help="Arquivo SQLite de saída.")
    args = parser.parse_args()
    counts = load_project_data(args.data_dir, args.db)
    print(f"Carga validada: {sum(counts.values()):,} registros em {args.db}")


if __name__ == "__main__":
    main()
