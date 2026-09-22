"""
Catalogo e mapeamento de metadados dos datasets do DHS Program para a África Subsaariana.
"""

import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional
import json
import csv

COUNTRY_MAP = {
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
    "OS": "África do Sul (Histórico/Outro)",
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

RECODE_MAP = {
    "IR": {
        "nome": "Mulheres (Individual Recode)",
        "descricao": "Dados individuais de mulheres (15-49 anos). Inclui saúde reprodutiva, maternidade, pré-natal, etc. [BÔNUS SAÚDE DA MULHER]",
        "categoria": "Saude_da_Mulher_IR"
    },
    "BR": {
        "nome": "Nascimentos (Births Recode)",
        "descricao": "Histórico de nascimentos das mulheres entrevistadas, partos, peso ao nascer e mortalidade infantil.",
        "categoria": "Nascimentos_BR"
    },
    "KR": {
        "nome": "Crianças (Children's Recode)",
        "descricao": "Crianças menores de 5 anos de idade, vacinação, nutrição, amamentação e episódios de doenças.",
        "categoria": "Criancas_KR"
    },
    "HR": {
        "nome": "Domicílios (Household Recode)",
        "descricao": "Características do domicílio, saneamento básico, fontes de água, bens e bens duráveis.",
        "categoria": "Domicilios_HR"
    },
    "PR": {
        "nome": "Moradores (Household Member Recode)",
        "descricao": "Informações demográficas de todos os moradores do domicílio (idade, sexo, educação).",
        "categoria": "Moradores_PR"
    },
    "CR": {
        "nome": "Casais (Couples Recode)",
        "descricao": "Dados conjuntos de casais casados ou vivendo em união estável.",
        "categoria": "Casais_CR"
    },
    "MR": {
        "nome": "Homens (Men's Recode)",
        "descricao": "Dados individuais de homens (15-49/59 anos), trabalho, saúde e conhecimentos reprodutivos.",
        "categoria": "Homens_MR"
    },
    "HW": {
        "nome": "Antropometria (Height and Weight)",
        "descricao": "Medições de altura, peso e escores nutricionais de mães e crianças.",
        "categoria": "Antropometria_HW"
    },
    "WI": {
        "nome": "Índice de Riqueza (Wealth Index)",
        "descricao": "Pontuação e quintil do índice de riqueza socioeconômica.",
        "categoria": "Riqueza_WI"
    },
    "SQ": {
        "nome": "Serviços de Saúde (Service Questionnaire)",
        "descricao": "Disponibilidade e infraestrutura dos serviços de saúde comunitários.",
        "categoria": "Servicos_Saude_SQ"
    },
    "HH": {
        "nome": "Inquérito Domiciliar (Household Survey)",
        "descricao": "Questionário domiciliar expandido / experimental.",
        "categoria": "Inquerito_Domiciliar_HH"
    },
    "IQ": {
        "nome": "Questionário Individual (Individual Questionnaire)",
        "descricao": "Questionários individuais específicos.",
        "categoria": "Questionario_Individual_IQ"
    },
    "ML": {
        "nome": "Malária (Malaria Module)",
        "descricao": "Módulo de prevenção, testes e tratamento de malária.",
        "categoria": "Malaria_ML"
    },
    "VA": {
        "nome": "Autópsia Verbal (Verbal Autopsy)",
        "descricao": "Inquérito para determinação de causa de morte.",
        "categoria": "Autopsia_Verbal_VA"
    },
    "OD": {
        "nome": "Outros Dados (Other Data)",
        "descricao": "Módulos complementares ou datasets especiais.",
        "categoria": "Outros_OD"
    },
}


def parse_dhs_url(url: str) -> Dict[str, str]:
    """Extrai informações estruturadas de uma URL do DHS Program."""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    filename = params.get("Filename", [""])[0]
    ctry_code = params.get("Ctry_Code", [""])[0]
    surv_id = params.get("surv_id", [""])[0]

    # Parsing filename (Ex: AOBR62DT.zip)
    # 2 letras: País, 2 letras: Recode, 2 dígitos: Fase/Versão, 2 letras: Formato (DT = Stata)
    recode_code = filename[2:4].upper() if len(filename) >= 4 else "XX"
    phase_version = filename[4:6] if len(filename) >= 6 else ""
    file_format = filename[6:8].upper() if len(filename) >= 8 else ""

    recode_info = RECODE_MAP.get(
        recode_code,
        {
            "nome": f"Recode {recode_code}",
            "descricao": "Dataset DHS",
            "categoria": f"Recode_{recode_code}"
        }
    )

    country_name = COUNTRY_MAP.get(ctry_code.upper(), f"País ({ctry_code})")

    return {
        "filename": filename,
        "country_code": ctry_code.upper(),
        "country_name": country_name,
        "recode_code": recode_code,
        "recode_name": recode_info["nome"],
        "recode_description": recode_info["descricao"],
        "category_folder": recode_info["categoria"],
        "phase_version": phase_version,
        "format": "Stata (.dta)" if file_format == "DT" else file_format,
        "surv_id": surv_id,
        "url": url,
        "relative_path": f"{country_name}/{recode_info['categoria']}/{filename}"
    }


def load_catalog(urls_file: str = "urls_dhs.txt") -> List[Dict[str, str]]:
    """Lê um arquivo de URLs ou o catálogo CSV exportado pelo projeto."""
    path = Path(urls_file)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de URLs não encontrado: {urls_file}")

    if path.suffix.lower() == ".csv":
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            return [row for row in csv.DictReader(f) if row.get("url")]

    catalog = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and line.startswith("http"):
                catalog.append(parse_dhs_url(line))
    return catalog


def export_catalog_files(urls_file: str = "urls_dhs.txt",
                         json_output: str = "catalogo_datasets.json",
                         csv_output: str = "catalogo_datasets.csv"):
    """Exporta o catálogo completo em JSON e CSV para apoiar o trabalho prático."""
    catalog = load_catalog(urls_file)

    # Exportar JSON
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    # Exportar CSV
    if catalog:
        fieldnames = list(catalog[0].keys())
        with open(csv_output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(catalog)

    print(f"Catálogo gerado com sucesso: {len(catalog)} datasets.")
    print(f" - JSON: {json_output}")
    print(f" - CSV:  {csv_output}")


if __name__ == "__main__":
    export_catalog_files()
