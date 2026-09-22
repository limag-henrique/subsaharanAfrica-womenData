"""Prepara a versão compacta dos microdados usados no projeto.

Mantém uma única onda (a de maior fase disponível) por país comparável,
seleciona somente os recodes do modelo integrado e grava CSVs gzip agregados
por recode. Os arquivos de origem não são alterados por este script.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import pyreadstat


KEEP_RECODES = ("IR", "BR", "HR", "PR", "KR", "HW", "CR", "MR", "SQ", "WI")
CORE_RECODES = {"IR", "BR", "HR", "PR", "KR"}

COUNTRY_NAMES = {
    "AO": "Angola",
    "BF": "Burkina Faso",
    "BJ": "Benin",
    "BU": "Burundi",
    "CD": "Congo (República Democrática)",
    "CF": "República Centro-Africana",
    "CG": "Congo (Brazzaville)",
    "CI": "Costa do Marfim",
    "CM": "Camarões",
    "ET": "Etiópia",
    "GA": "Gabão",
    "GH": "Gana",
    "GM": "Gâmbia",
    "GN": "Guiné",
    "KE": "Quênia",
    "KM": "Comores",
    "LB": "Libéria",
    "LS": "Lesoto",
    "MD": "Madagascar",
    "ML": "Mali",
    "MW": "Malaui",
    "MZ": "Moçambique",
    "NG": "Nigéria",
    "NI": "Níger",
    "NM": "Namíbia",
    "RW": "Ruanda",
    "SD": "Sudão",
    "SL": "Serra Leoa",
    "SN": "Senegal",
    "ST": "São Tomé e Príncipe",
    "SZ": "Eswatini (Suazilândia)",
    "TD": "Chade",
    "TG": "Togo",
    "TZ": "Tanzânia",
    "ZA": "África do Sul",
    "ZM": "Zâmbia",
    "ZW": "Zimbábue",
}


def file_parts(path: Path) -> tuple[str, str, str]:
    stem = path.stem.upper()
    return stem[:2], stem[2:4], stem[4:-2]


def phase_key(phase: str) -> tuple[int, str]:
    match = re.match(r"(\d+)(.*)", phase)
    return (int(match.group(1)), match.group(2)) if match else (-1, phase)


def unique_dta_files(source: Path) -> list[Path]:
    paths = [path for path in source.rglob("*") if path.is_file() and path.suffix.lower() == ".dta"]
    return list({str(path).lower(): path for path in paths}.values())


def select_latest_wave(files: Iterable[Path]) -> dict[str, Path]:
    latest_ir: dict[str, Path] = {}
    for path in files:
        country, recode, phase = file_parts(path)
        if country == "OS" or recode != "IR":
            continue
        if country not in latest_ir or phase_key(phase) > phase_key(file_parts(latest_ir[country])[2]):
            latest_ir[country] = path
    return latest_ir


def selected_files(files: Iterable[Path]) -> list[tuple[str, str, Path]]:
    files = list(files)
    latest_ir = select_latest_wave(files)
    result: list[tuple[str, str, Path]] = []
    for country, ir_path in sorted(latest_ir.items()):
        ir_phase = file_parts(ir_path)[2]
        for recode in KEEP_RECODES:
            candidates = [
                path
                for path in files
                if file_parts(path)[0] == country
                and file_parts(path)[1] == recode
            ]
            if recode in CORE_RECODES:
                candidates = [path for path in candidates if file_parts(path)[2] == ir_phase]
            if candidates:
                chosen = max(candidates, key=lambda path: phase_key(file_parts(path)[2]))
                result.append((country, file_parts(chosen)[2], chosen))
    return result


def explicit(*names: str) -> set[str]:
    return {name.lower() for name in names}


EXACT = {
    "IR": explicit(
        "caseid", "v001", "v002", "v003", "v005", "v006", "v007", "v008", "v008a",
        "v012", "v013", "v024", "v025", "v106", "v190", "v201", "v212", "v301",
        "v302", "v302a", "v312", "v313", "v445", "v453", "v457", "m3a_1", "m3b_1",
        "m4_1", "m5_1", "m13_1", "m14_1", "m15_1", "m17_1", "m18_1", "m19_1",
        "m34_1", "m35_1", "m36_1", "m38_1", "m39_1",
    ),
    "BR": explicit(
        "caseid", "bidx", "bord", "v001", "v002", "v003", "v005", "b0", "b1", "b2",
        "b3", "b4", "b5", "b6", "b7", "b8", "b9", "b10", "b11", "b12", "b13",
        "b15", "b16", "b17", "b18", "b19", "b20", "b21", "m3a", "m3b", "m4", "m5",
        "m6", "m7", "m13", "m14", "m15", "m17", "m18", "m19", "m34", "m35", "m36",
        "m38", "m39a",
    ),
    "HR": explicit(
        "hhid", "hv001", "hv002", "hv003", "hv005", "hv009", "hv012", "hv013", "hv024",
        "hv025", "hv201", "hv205", "hv206", "hv207", "hv208", "hv209", "hv210", "hv211",
        "hv212", "hv213", "hv214", "hv215", "hv216", "hv217", "hv218", "hv219", "hv220",
        "hv221", "hv222", "hv223", "hv225", "hv226", "hv227", "hv228", "hv230a", "hv232",
        "hv234", "hv235", "hv236a", "hv237", "hv240", "hv270", "hv271",
    ),
    "PR": explicit(
        "hhid", "hvidx", "hv001", "hv002", "hv003", "hv004", "hv005", "hv009", "hv012",
        "hv013", "hv024", "hv025", "hv101", "hv102", "hv103", "hv104", "hv105", "hv106",
        "hv107", "hv108", "hv109", "hv110", "hv111", "hv112", "hv113", "hv114", "hv115",
        "hv116", "hv117", "hv118", "hv120", "hv121", "hv122", "hv123", "hv124", "hv125",
        "hv126", "hv127", "hv128", "hv129",
    ),
    "KR": explicit(
        "caseid", "bidx", "bidxp", "v001", "v002", "v003", "v005", "b0", "b1", "b2", "b3",
        "b4", "b5", "b6", "b7", "b8", "b9", "b10", "b11", "b12", "h1", "h2", "h3", "h4",
        "h5", "h6", "h7", "h8", "h9", "h10", "h11", "h12", "h13", "h22", "h31", "h34",
        "h39", "h40", "h42", "h43", "h44", "m4", "m5", "m6", "m7", "m13", "m14", "m15",
        "m17", "m18", "m19", "m34", "m35", "m36", "m38", "m39a",
    ),
    "CR": explicit(
        "caseid", "v001", "v002", "v003", "v005", "v012", "v024", "v025", "v106", "v190",
        "mv001", "mv002", "mv003", "mv005", "mv012", "mv024", "mv025", "mv106", "mv190",
    ),
    "MR": explicit(
        "mcaseid", "mv001", "mv002", "mv003", "mv005", "mv012", "mv024", "mv025", "mv106",
        "mv190", "mv201", "mv212",
    ),
    "HW": explicit("hwhhid", "hwline", "hwlevel", "hc70", "hc71", "hc72", "hc73"),
    "WI": explicit("whhid", "wlthindf", "wlthind5"),
}


def choose_columns(recode: str, available: list[str]) -> list[str]:
    available_by_lower = {name.lower(): name for name in available}
    chosen = {available_by_lower[name] for name in EXACT.get(recode, set()) if name in available_by_lower}
    if recode == "IR":
        chosen.update(name for name in available if re.match(r"^v30[457]_", name, re.I))
        chosen.update(name for name in available if re.match(r"^v30[457]a?_$", name, re.I))
    if recode == "SQ":
        chosen.update(name for name in available if name.lower().startswith("sq"))
        chosen.update(
            name for name in available
            if re.match(
                r"^(grappe|zd|dep|com|arrond|urbrur|vil|jour|mois|annee|cequipe|cresul|nsec[12]|"
                r"q10[1-9]a?|q11[01]a?|sq(prov|depart|grappe|local|nom|nbhab|denq[jm]|"
                r"fenq[jm]|numenq|nbenqh|depeds|10[2-9]|11[0-5]|20[1-8]))$",
                name,
                re.I,
            )
        )
        if not chosen:
            # Alguns questionários de serviço usam nomes locais sem o prefixo SQ.
            # Preservamos apenas o cabeçalho inicial, que contém a identificação
            # do serviço e os primeiros indicadores, em vez de descartar o arquivo.
            chosen.update(available[:40])
    return [name for name in available if name in chosen]


def add_identifier(frame: pd.DataFrame, name: str, parts: list[str]) -> None:
    if not all(part in frame.columns for part in parts):
        frame[name] = pd.Series(pd.NA, index=frame.index, dtype="string")
        return
    values = [frame[part].astype("string").fillna("") for part in parts]
    frame[name] = values[0]
    for value in values[1:]:
        frame[name] = frame[name] + "|" + value


def enrich(frame: pd.DataFrame, country: str, phase: str, recode: str, source: Path) -> pd.DataFrame:
    frame.insert(0, "pais_codigo", country)
    frame.insert(1, "pais_nome", COUNTRY_NAMES[country])
    frame.insert(2, "levantamento_id", f"{country}_{phase}")
    frame.insert(3, "fase", phase)
    frame.insert(4, "arquivo_origem", source.name)
    frame.insert(5, "linha_origem", range(1, len(frame) + 1))

    if recode in {"IR", "BR", "KR", "CR"}:
        add_identifier(frame, "id_mulher", ["caseid"])
        add_identifier(frame, "id_domicilio", ["v001", "v002"])
    if recode == "IR":
        add_identifier(frame, "id_mulher_global", ["pais_codigo", "levantamento_id", "caseid"])
    elif recode == "BR":
        add_identifier(frame, "id_nascimento", ["caseid", "bidx"])
    elif recode == "KR":
        add_identifier(frame, "id_crianca", ["caseid", "bidx"])
    elif recode == "HR":
        add_identifier(frame, "id_domicilio", ["hhid"])
    elif recode == "PR":
        add_identifier(frame, "id_domicilio", ["hhid"])
        add_identifier(frame, "id_morador", ["hhid", "hvidx"])
    elif recode == "CR":
        add_identifier(frame, "id_casal", ["caseid"])
    elif recode == "MR":
        add_identifier(frame, "id_parceiro", ["mcaseid"])
    elif recode == "HW":
        add_identifier(frame, "id_medicao", ["hwhhid", "hwline"])
    elif recode == "WI":
        add_identifier(frame, "id_domicilio", ["whhid"])
    elif recode == "SQ":
        if "sqgrappe" in frame.columns:
            add_identifier(frame, "id_servico", ["sqgrappe", "sqprov", "sqdepart", "sqlocal"])
        else:
            add_identifier(frame, "id_servico", ["grappe", "zd", "dep", "com"])
    return frame


def prepare(source: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("*.csv.gz"):
        old.unlink()
    selected = selected_files(unique_dta_files(source))
    manifest_rows: list[dict[str, object]] = []
    output_headers: dict[str, bool] = {}

    for country, phase, path in selected:
        _, recode, _ = file_parts(path)
        _, metadata = pyreadstat.read_dta(str(path), metadataonly=True, encoding="latin1")
        columns = choose_columns(recode, metadata.column_names)
        if not columns:
            continue
        data, _ = pyreadstat.read_dta(str(path), usecols=columns, encoding="latin1")
        data = enrich(data, country, phase, recode, path)
        target = output / f"{recode}.csv.gz"
        with gzip.open(target, mode="at", encoding="utf-8", newline="") as handle:
            data.to_csv(handle, index=False, header=not output_headers.get(recode, False))
        output_headers[recode] = True
        manifest_rows.append(
            {
                "pais_codigo": country,
                "pais_nome": COUNTRY_NAMES[country],
                "fase": phase,
                "recode": recode,
                "arquivo_origem": path.name,
                "caminho_origem": str(path),
                "linhas": len(data),
                "colunas_selecionadas": len(columns),
                "colunas": "|".join(columns),
            }
        )
        print(f"[{recode}] {country} fase {phase}: {len(data):,} linhas, {len(columns)} colunas")

    with (output / "manifesto_selecao.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    (output / "README.md").write_text(
        "# Dados compactos do projeto\n\n"
        "Esta pasta contém apenas uma onda recente por país comparável (exclui `OS`, "
        "África do Sul histórica), os recodes do modelo integrado e as variáveis "
        "necessárias às entidades e relacionamentos. Os cinco recodes centrais "
        "(IR/BR/HR/PR/KR) usam a mesma fase; os módulos opcionais usam a fase mais "
        "recente disponível e só devem ser unidos quando as chaves forem compatíveis. "
        "Os arquivos estão em CSV gzip.\n\n"
        "Consulte `manifesto_selecao.csv` para a origem, fase, quantidade de linhas e "
        "colunas de cada arquivo. Os microdados brutos não devem ser versionados.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("dados/completo/extraidos"))
    parser.add_argument("--output", type=Path, default=Path("dados/relevantes"))
    args = parser.parse_args()
    prepare(args.source, args.output)


if __name__ == "__main__":
    main()
