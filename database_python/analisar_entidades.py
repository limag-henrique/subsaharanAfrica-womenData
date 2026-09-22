"""Audita metadados dos microdados DHS e produz relatórios de padronização.

O script usa apenas o cabeçalho/metadados dos arquivos Stata. Assim, a análise
de cobertura não precisa carregar os quase 10 GB de observações em memória.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import pandas as pd


THEMES = {
    "violencia_genero_autonomia": "Violência, abuso e autonomia",
    "saude_materna": "Saúde materna e assistência ao parto",
    "planejamento_familiar": "Planejamento familiar e contracepção",
    "saude_sexual_ist": "Saúde sexual, HIV/IST e tuberculose",
    "nutricao_anemia": "Nutrição, antropometria e anemia",
    "saude_infantil": "Saúde infantil e aleitamento",
    "historia_reprodutiva": "História reprodutiva e fecundidade",
    "socioeconomico": "Condições socioeconômicas e domicílio",
    "demografia": "Demografia e contexto geográfico",
    "identificacao_amostragem": "Identificação, amostragem e entrevista",
    "outros": "Outros módulos/variáveis",
}

RECODE_GUIDE = {
    "IR": ("mulher_nucleo", "Entrevista individual da mulher; fonte principal"),
    "BR": ("gestacao_parto", "Nascimentos, gestações e histórico obstétrico"),
    "HR": ("domicilio_contexto", "Domicílio, saneamento, bens e contexto"),
    "PR": ("moradores_contexto", "Moradores do domicílio e composição familiar"),
    "HW": ("antropometria", "Peso, altura, anemia e medidas corporais"),
    "KR": ("saude_infantil", "Saúde, nutrição e vacinação de crianças"),
    "CR": ("casal_parceiro", "Informações conjugais e do parceiro"),
    "MR": ("casal_parceiro", "Informações masculinas relacionadas ao casal"),
    "SQ": ("servicos_saude", "Disponibilidade e infraestrutura de serviços"),
    "WI": ("socioeconomico", "Índice de riqueza e contexto socioeconômico"),
    "ML": ("malaria", "Prevenção, diagnóstico e tratamento de malária"),
    "VA": ("mortalidade", "Autópsia verbal e causa de morte"),
    "HH": ("modulo_especial", "Questionário domiciliar especial"),
    "IQ": ("modulo_especial", "Questionário individual especial"),
    "OD": ("modulo_especial", "Outros dados/módulos complementares"),
    "DV": ("violencia_genero", "Módulo de violência doméstica"),
    "OL": ("adolescencia", "Módulo relacionado à adolescência"),
    "IA": ("saude_infantil", "Módulo relacionado à infância"),
    "AT": ("mortalidade", "Certificados de óbito; usar apenas se pertinente"),
    "HA": ("modulo_especial", "Módulo auxiliar; validar pelo dicionário"),
    "HB": ("modulo_especial", "Módulo auxiliar; validar pelo dicionário"),
}


def normalize_text(value: object) -> str:
    """Normaliza texto para comparação, removendo marcadores DHS de NA."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"\b(?:na|n/a)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify_theme(variable: str, label: str) -> str:
    text = normalize_text(f"{variable} {label}")
    patterns = (
        (
            "violencia_genero_autonomia",
            r"violence|abuse|beaten|slap|punch|push|kick|hurt|rape|forced sex|"
            r"domestic|injur|bruise|humiliat|threaten|insult|permission to go|"
            r"decision maker",
        ),
        (
            "saude_materna",
            r"antenatal|prenatal|delivery|delivered|birth attendant|place of delivery|"
            r"postnatal|cesarean|caesarean|tetanus|pregnan|maternal|obstetric",
        ),
        (
            "planejamento_familiar",
            r"contracept|family planning|steriliz|method use|fertility preference|"
            r"desire for children",
        ),
        (
            "saude_sexual_ist",
            r"hiv|aids|sexually transmitted|\bsti\b|\bstd\b|tuberculosis|"
            r"sexual partner|sexual activity|condom",
        ),
        (
            "nutricao_anemia",
            r"anemia|haemoglobin|hemoglobin|body mass|\bbmi\b|weight|height|"
            r"arm circumference|nutrition",
        ),
        (
            "saude_infantil",
            r"breastfeed|vaccin|diarrhea|diarrhoea|fever|child health|child illness|"
            r"oral rehydration",
        ),
        (
            "historia_reprodutiva",
            r"birth|born|fertility|child|pregnancy history|menstru|abortion|"
            r"miscarriage|stillbirth|live children",
        ),
        (
            "socioeconomico",
            r"education|literacy|occupation|employ|work|wealth|floor|wall|roof|"
            r"water|toilet|electric|radio|television|refrigerator|asset|household",
        ),
        (
            "demografia",
            r"age|marital|marriage|residence|region|district|religion|ethnic|"
            r"language|orphan|relationship",
        ),
        (
            "identificacao_amostragem",
            r"case|cluster|household|line number|sample weight|interview|"
            r"enumeration|identification|respondent|interviewer|questionnaire|"
            r"time|visit",
        ),
    )
    for theme, pattern in patterns:
        if re.search(pattern, text):
            return theme
    return "outros"


def catalog_stem(filename: str) -> str:
    """Converte o nome de pacote DHS (...DT.zip) em stem do arquivo (...FL)."""
    stem = Path(filename).stem.upper()
    return f"{stem[:6]}FL"


def read_catalog(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def collect_metadata(raw_root: Path, catalog: Iterable[dict[str, str]]):
    catalog_by_stem = {catalog_stem(row["filename"]): row for row in catalog}
    file_rows: list[dict[str, object]] = []
    country_variables: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    theme_country_variables: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )

    dta_paths = sorted(path for path in raw_root.rglob("*") if path.suffix.lower() == ".dta")
    for path in dta_paths:
        reader = pd.read_stata(path, iterator=True, convert_categoricals=False)
        labels = reader.variable_labels()
        stem = path.stem.upper()
        catalog_row = catalog_by_stem.get(stem, {})
        relative_parts = path.relative_to(raw_root).parts
        country = catalog_row.get("country_name") or relative_parts[0]
        if country == "África do Sul (Histórico" and len(relative_parts) > 1:
            country = "África do Sul (Histórico/Outro)"
        recode = stem[2:4]
        category, role = RECODE_GUIDE.get(
            recode, ("modulo_nao_mapeado", "Validar pelo dicionário do survey")
        )
        file_rows.append(
            {
                "country": country,
                "file": path.name,
                "stem": stem,
                "recode": recode,
                "women_health_category": category,
                "women_health_role": role,
                "phase_version": stem[4:6],
                "variables": len(labels),
                "catalog_filename": catalog_row.get("filename", ""),
                "survey_id": catalog_row.get("surv_id", ""),
                "data_label": getattr(reader, "data_label", "") or "",
            }
        )
        for variable, raw_label in labels.items():
            label = str(raw_label or "")
            theme = classify_theme(variable, label)
            current = country_variables[country].setdefault(
                variable,
                {"files": set(), "labels": set(), "themes": set()},
            )
            current["files"].add(path.name)
            current["labels"].add(label)
            current["themes"].add(theme)
            theme_country_variables[theme][country].add(variable)
        del reader

    return file_rows, country_variables, theme_country_variables, dta_paths


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", default="dados/brutos")
    parser.add_argument("--catalog", default="catalogo_datasets.csv")
    parser.add_argument("--output", default="analises")
    args = parser.parse_args()

    raw_root = Path(args.raw_root)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    catalog = read_catalog(Path(args.catalog))
    file_rows, country_variables, theme_country_variables, dta_paths = collect_metadata(
        raw_root, catalog
    )
    countries = sorted(country_variables)
    country_sets = {country: set(values) for country, values in country_variables.items()}
    exact_common = set.intersection(*(values for values in country_sets.values()))

    write_csv(
        output / "inventario_arquivos.csv",
        file_rows,
        [
            "country",
            "file",
            "stem",
            "recode",
            "women_health_category",
            "women_health_role",
            "phase_version",
            "variables",
            "catalog_filename",
            "survey_id",
            "data_label",
        ],
    )

    presence_rows = []
    for country in countries:
        for variable, info in sorted(country_variables[country].items()):
            labels = sorted(label for label in info["labels"] if label)
            presence_rows.append(
                {
                    "country": country,
                    "variable": variable,
                    "files_with_variable": len(info["files"]),
                    "country_files": len([row for row in file_rows if row["country"] == country]),
                    "labels": " | ".join(labels),
                    "normalized_labels": " | ".join(sorted({normalize_text(label) for label in labels})),
                    "themes": " | ".join(sorted(info["themes"])),
                    "in_all_countries": variable in exact_common,
                }
            )
    write_csv(
        output / "presenca_variaveis_por_pais.csv",
        presence_rows,
        [
            "country",
            "variable",
            "files_with_variable",
            "country_files",
            "labels",
            "normalized_labels",
            "themes",
            "in_all_countries",
        ],
    )

    variable_country_count = Counter(
        variable for values in country_sets.values() for variable in values
    )
    common_rows = []
    for variable in sorted(exact_common):
        labels = sorted(
            {
                label
                for country in countries
                for label in country_variables[country][variable]["labels"]
                if label
            }
        )
        common_rows.append(
            {
                "variable": variable,
                "country_count": variable_country_count[variable],
                "file_count": sum(
                    len(country_variables[country][variable]["files"])
                    for country in countries
                ),
                "labels": " | ".join(labels),
                "themes": " | ".join(
                    sorted(
                        {
                            theme
                            for country in countries
                            for theme in country_variables[country][variable]["themes"]
                        }
                    )
                ),
            }
        )
    write_csv(
        output / "variaveis_comuns_37_paises.csv",
        common_rows,
        ["variable", "country_count", "file_count", "labels", "themes"],
    )
    write_csv(
        output / "variaveis_comuns_todos_paises.csv",
        common_rows,
        ["variable", "country_count", "file_count", "labels", "themes"],
    )

    label_countries: dict[str, set[str]] = defaultdict(set)
    label_variables: dict[str, set[str]] = defaultdict(set)
    label_examples: dict[str, set[str]] = defaultdict(set)
    for country in countries:
        for variable, info in country_variables[country].items():
            for label in info["labels"]:
                normalized = normalize_text(label)
                if not normalized:
                    continue
                label_countries[normalized].add(country)
                label_variables[normalized].add(variable)
                label_examples[normalized].add(label)
    label_rows = []
    for normalized, seen_countries in sorted(label_countries.items()):
        label_rows.append(
            {
                "normalized_label": normalized,
                "country_count": len(seen_countries),
                "variable_count": len(label_variables[normalized]),
                "countries": " | ".join(sorted(seen_countries)),
                "variables": " | ".join(sorted(label_variables[normalized])),
                "examples": " | ".join(sorted(label_examples[normalized])[:8]),
            }
        )
    write_csv(
        output / "denominacoes_normalizadas.csv",
        label_rows,
        [
            "normalized_label",
            "country_count",
            "variable_count",
            "countries",
            "variables",
            "examples",
        ],
    )
    write_csv(
        output / "denominacoes_comuns_todos_paises.csv",
        [row for row in label_rows if row["country_count"] == len(countries)],
        [
            "normalized_label",
            "country_count",
            "variable_count",
            "countries",
            "variables",
            "examples",
        ],
    )

    theme_rows = []
    for theme, country_map in sorted(theme_country_variables.items()):
        theme_rows.append(
            {
                "theme": theme,
                "description": THEMES[theme],
                "country_count": len(country_map),
                "variable_country_pairs": sum(len(values) for values in country_map.values()),
                "countries_missing": " | ".join(sorted(set(countries) - set(country_map))),
                "representative_variables": " | ".join(
                    sorted(set().union(*country_map.values()))[:20]
                ),
            }
        )
    write_csv(
        output / "cobertura_temas.csv",
        theme_rows,
        [
            "theme",
            "description",
            "country_count",
            "variable_country_pairs",
            "countries_missing",
            "representative_variables",
        ],
    )

    catalog_recode_rows = []
    catalog_by_country: dict[str, Counter[str]] = defaultdict(Counter)
    for row in catalog:
        catalog_by_country[row["country_name"]][row["recode_code"]] += 1
    for country, recodes in sorted(catalog_by_country.items()):
        for recode, count in sorted(recodes.items()):
            catalog_recode_rows.append(
                {"country": country, "recode": recode, "dataset_count": count}
            )
    write_csv(
        output / "cobertura_recodes_catalogo.csv",
        catalog_recode_rows,
        ["country", "recode", "dataset_count"],
    )

    local_recode_counts = Counter(row["recode"] for row in file_rows)
    recode_rows = []
    observed_recodes = sorted(
        set(row["recode_code"] for row in catalog) | set(local_recode_counts)
    )
    for recode in observed_recodes:
        category, role = RECODE_GUIDE.get(
            recode, ("modulo_nao_mapeado", "Validar pelo dicionário do survey")
        )
        catalog_count = sum(row["recode_code"] == recode for row in catalog)
        local_count = local_recode_counts.get(recode, 0)
        recode_rows.append(
            {
                "recode": recode,
                "women_health_category": category,
                "women_health_role": role,
                "catalog_dataset_count": catalog_count,
                "local_dta_count": local_count,
                "recommended": category != "modulo_nao_mapeado",
            }
        )
    write_csv(
        output / "classificacao_recodes_saude_mulher.csv",
        recode_rows,
        [
            "recode",
            "women_health_category",
            "women_health_role",
            "catalog_dataset_count",
            "local_dta_count",
            "recommended",
        ],
    )

    violence_terms = re.compile(
        r"violence|abuse|beaten|slap|punch|push|kick|hurt|rape|forced sex|domestic|"
        r"injur|bruise|humiliat|threaten|insult",
        re.I,
    )
    semantic_families = {
        "violencia_fisica": re.compile(
            r"physical violence|physically hurt|slapped|punched|kicked|pushed|"
            r"bruis|wounds|injur|hit by something",
            re.I,
        ),
        "violencia_emocional": re.compile(
            r"emotional violence|emotional abuse|humiliat|threaten|insult|feel bad",
            re.I,
        ),
        "violencia_sexual": re.compile(
            r"sexual violence|forced sexual|forced sex|\brape\b", re.I
        ),
        "autonomia_e_decisao": re.compile(
            r"decision maker|permission to go|getting medical help for self", re.I
        ),
    }
    semantic_rows = []
    all_label_records = []
    for country in countries:
        for variable, info in country_variables[country].items():
            for label in info["labels"]:
                all_label_records.append((country, variable, label))
    for family, pattern in semantic_families.items():
        records = [record for record in all_label_records if pattern.search(record[2])]
        family_countries = {record[0] for record in records}
        family_labels = Counter(normalize_text(record[2]) for record in records)
        examples = [label for label, _ in family_labels.most_common(8) if label]
        semantic_rows.append(
            {
                "semantic_family": family,
                "country_count": len(family_countries),
                "variable_count": len({record[1] for record in records}),
                "country_variable_pairs": len({(record[0], record[1]) for record in records}),
                "representative_normalized_labels": " | ".join(examples),
                "countries_missing": " | ".join(sorted(set(countries) - family_countries)),
            }
        )
    write_csv(
        output / "familias_semanticas.csv",
        semantic_rows,
        [
            "semantic_family",
            "country_count",
            "variable_count",
            "country_variable_pairs",
            "representative_normalized_labels",
            "countries_missing",
        ],
    )

    raw_stems = {path.stem.upper() for path in dta_paths}
    catalog_stems = {catalog_stem(row["filename"]) for row in catalog}
    catalog_missing_local = sorted(catalog_stems - raw_stems)
    local_recode_summary = ", ".join(
        f"{recode}={count}" for recode, count in sorted(local_recode_counts.items())
    )
    only_ir = set(local_recode_counts) == {"IR"}
    dataset_scope = "levantamentos IR" if only_ir else "arquivos Stata extraídos"
    violence_country_count = len(theme_country_variables["violencia_genero_autonomia"])
    violence_missing = sorted(
        set(countries) - set(theme_country_variables["violencia_genero_autonomia"])
    )
    report_lines = [
        "# Auditoria de entidades e denominações dos dados DHS",
        "",
        "## Escopo e método",
        "",
        f"- Foram encontrados **{len(countries)} países**, **{len(dta_paths)} arquivos `.DTA`** e **{sum(path.stat().st_size for path in dta_paths) / (1024**3):.2f} GiB** de microdados locais.",
        f"- A análise foi feita pelos metadados Stata (nomes de variáveis e rótulos), sem carregar as observações completas.",
        f"- O catálogo contém **{len(catalog)} pacotes**, dos quais **{sum(row['recode_code'] == 'IR' for row in catalog)} IR**; a pasta analisada contém os recodes listados abaixo.",
        f"- Os recodes encontrados na pasta analisada são: **{local_recode_summary}**.",
        f"- Foram encontradas **{len(raw_stems & catalog_stems)} correspondências** entre os stems locais e o catálogo; a diferença de nomes ocorre porque o pacote usa sufixo `DT` e o arquivo extraído usa `FL`.",
        f"- Pacotes do catálogo sem `.DTA` local: **{', '.join(catalog_missing_local) if catalog_missing_local else 'nenhum'}**.",
        "",
        "## Resultado principal",
        "",
        f"Cada país possui entre **{min(len(values) for values in country_sets.values()):,}** e **{max(len(values) for values in country_sets.values()):,}** variáveis distintas no conjunto de seus {dataset_scope}.",
        f"Há **{len(exact_common)} nomes de variáveis exatamente iguais** presentes em todos os {len(countries)} países. A lista completa está no arquivo `variaveis_comuns_37_paises.csv`.",
        "",
        "As denominações compartilhadas não devem ser comparadas apenas pelo texto bruto: o DHS mantém códigos estáveis (por exemplo, `v012`, `v106`, `v201`, `v312`) enquanto os rótulos mudam com abreviações, idioma do questionário, `NA` e versões do levantamento. A lista completa normalizada está em `denominacoes_normalizadas.csv`; a interseção universal está em `denominacoes_comuns_todos_paises.csv`.",
        "",
        "### Núcleo comum de entidades/conceitos",
        "",
        "- Identificação e amostragem: `caseid`, país/fase, cluster, domicílio, linha da respondente, peso amostral e datas da entrevista.",
        "- Demografia: idade, grupos etários, nascimento, região e situação urbana/rural.",
        "- Educação e contexto: nível/anos de escolaridade, alfabetização, água, banheiro e material do domicílio.",
        "- História reprodutiva: filhos nascidos, filhos vivos, gravidez atual, nascimentos recentes e histórico de nascimentos (`b0`–`b12`).",
        "- Saúde reprodutiva: gravidez, contracepção e intenção/desejo de filhos.",
        "- Entrevista: completude, duração, visitas e identificação da entrevistadora.",
        "",
        "## Entidades canônicas para o modelo relacional",
        "",
        "Os `.DTA` são arquivos de microdados, não um esquema relacional pronto; por isso, “entidade” aqui significa um conceito que pode ser normalizado em tabela:",
        "",
        "- `Pais`: código/onda e região do país; funciona como dimensão de comparação.",
        "- `Mulher`: `caseid` e atributos demográficos, educacionais, reprodutivos e de saúde da entrevistada; nasce principalmente de `IR`.",
        "- `Domicilio`: cluster, domicílio, residência, riqueza, água, banheiro e bens; combina `IR`, `HR` e `PR` quando necessário.",
        "- `Gestacao_Parto_Nascimento`: gravidez, pré-natal, local/assistência do parto e histórico de nascimentos; combina `IR` e `BR`.",
        "- `Metodo_Contraceptivo`: catálogo/dimensões de método e uso atual; atributos centrais em `IR`.",
        "- `Violencia_Autonomia`: bloco opcional das variáveis `d*`/módulo de violência e decisões/permissão; não deve ser criado como entidade presente em todos os países.",
        "- `Crianca` e `Servico_Saude`: entidades opcionais vindas de `KR`/`HW` e `SQ`, conforme a pergunta analítica.",
        "",
        "## Equivalência semântica",
        "",
        "Foi aplicada normalização de caixa, acentos, pontuação, espaços e marcadores `NA`. Para não misturar fenômenos distintos, as equivalências foram agrupadas por família temática; os resultados estão em [familias_semanticas.csv](familias_semanticas.csv).",
        "",
        "- Violência física: `physical violence`, `physically hurt`, `slapped`, `punched`, `kicked`, `pushed`, ferimentos e hematomas.",
        "- Violência emocional: `emotional violence/abuse`, humilhação, ameaça, insulto e fazer a mulher se sentir mal.",
        "- Violência sexual: `sexual violence`, `forced sexual act/sex` e estupro/violação quando o rótulo aparece.",
        "- Autonomia e controle: decisão sobre contracepção e permissão para buscar atendimento médico. Esses rótulos são relacionados à autonomia de gênero, mas não devem ser contabilizados automaticamente como agressão física ou abuso.",
        "",
        f"O módulo de violência/autonomia aparece em **{violence_country_count} dos {len(countries)} países**; os grupos sem rótulos correspondentes são **{', '.join(violence_missing) if violence_missing else 'nenhum'}**. Isso é cobertura de questionário, não uma conclusão de que não existe violência nesses países.",
        "",
        "## A separação atual está correta?",
        "",
        "A seleção `IR` está tecnicamente correta para mulheres entrevistadas de 15–49 anos e contém grande parte da saúde reprodutiva, materna, contracepção, HIV/IST e violência doméstica. Contudo, classificá-la como o conjunto completo de saúde da mulher é incompleto: parto/nascimento, domicílio, antropometria, crianças, serviços e módulos especiais estão distribuídos em outros recodes.",
        "",
        "A categorização recomendada é manter `IR` como tabela/fonte central da mulher e adicionar, conforme a pergunta analítica, `BR` (nascimentos), `HR`/`PR` (domicílio e moradores), `HW` (antropometria), `KR` (criança), e módulos `SQ`, `ML`, `VA`, `HH`, `IQ` ou `OD` somente quando existirem no país e forem necessários. A cobertura por país e recode está em [cobertura_recodes_catalogo.csv](cobertura_recodes_catalogo.csv).",
        "",
        "A classificação operacional por recode e por arquivo está em [classificacao_recodes_saude_mulher.csv](classificacao_recodes_saude_mulher.csv) e [inventario_arquivos.csv](inventario_arquivos.csv). Módulos auxiliares fora do catálogo principal foram marcados como `modulo_nao_mapeado` ou `modulo_especial` e devem ser validados pelo dicionário antes de entrar no modelo relacional.",
        "",
        "## Possibilidade de repetir o download",
        "",
        "- O login DHS foi testado com as credenciais já configuradas em `.env` e foi aceito; um projeto aprovado foi selecionado.",
        "- O fluxo foi corrigido para ler `catalogo_datasets.csv`, que contém as 1.419 URLs, em vez de depender do inexistente `urls_dhs.txt`.",
        "- A repetição completa é operacionalmente possível com `--urls-file catalogo_datasets.csv`; ela deve ser feita para uma pasta separada, pois o catálogo é muito maior que o subconjunto IR local.",
        "- O download completo pode consumir dezenas de gigabytes e tempo significativo. A análise atual não baixa novamente arquivos que já foram auditados; ela deixa o fluxo pronto para execução autenticada e preserva o conjunto local original.",
        "",
        "## Artefatos",
        "",
        "- [inventario_arquivos.csv](inventario_arquivos.csv): um registro por `.DTA` local.",
        "- [presenca_variaveis_por_pais.csv](presenca_variaveis_por_pais.csv): presença, rótulos e temas por país/variável.",
        "- [variaveis_comuns_37_paises.csv](variaveis_comuns_37_paises.csv): interseção exata dos nomes (o sufixo do nome preserva o artefato original).",
        "- [variaveis_comuns_todos_paises.csv](variaveis_comuns_todos_paises.csv): cópia com nome independente do número de países.",
        "- [denominacoes_normalizadas.csv](denominacoes_normalizadas.csv): rótulos após normalização.",
        "- [denominacoes_comuns_todos_paises.csv](denominacoes_comuns_todos_paises.csv): somente as denominações presentes em todos os grupos.",
        "- [cobertura_temas.csv](cobertura_temas.csv) e [familias_semanticas.csv](familias_semanticas.csv): cobertura temática e equivalência semântica.",
        "- [cobertura_recodes_catalogo.csv](cobertura_recodes_catalogo.csv): recodes disponíveis no catálogo por país.",
        "- [classificacao_recodes_saude_mulher.csv](classificacao_recodes_saude_mulher.csv): categorização operacional para o escopo mulher.",
    ]
    (output / "relatorio_entidades_saude_mulher.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    print(f"Países analisados: {len(countries)}")
    print(f"Arquivos DTA analisados: {len(dta_paths)}")
    print(f"Variáveis comuns a todos os países: {len(exact_common)}")
    print(
        "Cobertura de violência/autonomia:",
        len(theme_country_variables["violencia_genero_autonomia"]),
        "de",
        len(countries),
    )
    print(f"Relatório: {output / 'relatorio_entidades_saude_mulher.md'}")


if __name__ == "__main__":
    main()
