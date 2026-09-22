"""
Script principal para download e organização dos datasets do DHS Program (África Subsaariana).

Este script atende aos requisitos do Trabalho Prático da disciplina DCC011 (Introdução a Banco de Dados),
permitindo baixar, autenticar, validar e organizar sistematicamente os microdados de saúde.

Suporta:
- Autenticação via login/senha DHS ou via Cookie de sessão ativa do navegador.
- Filtros por país, tipo de questionário (ex: IR - Saúde da Mulher), e limite de downloads.
- Organização em pastas hierárquicas: dados/brutos/{País}/{Categoria}/{Arquivo.zip}.
- Extração opcional dos arquivos Stata (.dta).
- Verificação de integridade (impede que páginas HTML de login sejam salvas como zip).
"""

import os
import sys
import getpass
import zipfile
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from catalogo import load_catalog, COUNTRY_MAP, RECODE_MAP

# Carrega credenciais do arquivo .env automaticamente se existir
load_dotenv()

DHS_LOGIN_URL = "https://dhsprogram.com/data/dataset_admin/login_main.cfm"
DHS_INDEX_URL = "https://dhsprogram.com/data/dataset_admin/index.cfm"
DHS_API_DATASETS_URL = "https://api.dhsprogram.com/rest/dhs/datasets"
DEFAULT_OUTPUT_DIR = "dados"


class DHSApiClient:
    """Consulta metadados públicos do DHS para validar os ZIPs solicitados.

    A API pública fornece catálogo, tamanho e formato; os microdados continuam
    protegidos e são baixados pela sessão autenticada do portal DHS.
    """

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self._country_cache: Dict[str, Dict[str, Dict]] = {}

    def _get_country_metadata(self, country_code: str) -> Dict[str, Dict]:
        country_code = country_code.upper()
        if country_code not in self._country_cache:
            response = self.session.get(
                DHS_API_DATASETS_URL,
                params={"f": "json", "countryIds": country_code, "perpage": 1000},
                timeout=30,
            )
            response.raise_for_status()
            records = response.json().get("Data", [])
            self._country_cache[country_code] = {
                record.get("FileName", "").upper(): record
                for record in records
                if record.get("FileName")
            }
        return self._country_cache[country_code]

    def enrich(self, items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Acrescenta metadados da API sem impedir o download se ela falhar."""
        enriched = []
        countries = sorted({item["country_code"].upper() for item in items})
        metadata_by_country: Dict[str, Dict[str, Dict]] = {}

        for country_code in countries:
            try:
                metadata_by_country[country_code] = self._get_country_metadata(country_code)
            except requests.RequestException:
                metadata_by_country[country_code] = {}

        for item in items:
            record = metadata_by_country[item["country_code"].upper()].get(item["filename"].upper())
            enriched_item = dict(item)
            if record:
                enriched_item.update({
                    "expected_size": record.get("FileSize"),
                    "api_file_type": record.get("FileType"),
                    "api_file_format": record.get("FileFormat"),
                    "api_validation": "ENCONTRADO",
                })
            else:
                enriched_item["api_validation"] = "NAO_ENCONTRADO"
            enriched.append(enriched_item)
        return enriched


class DHSDownloader:
    DEFAULT_WORKERS = 1

    def __init__(self, username: Optional[str] = None,
                 password: Optional[str] = None,
                 cookie_str: Optional[str] = None,
                 output_dir: str = DEFAULT_OUTPUT_DIR,
                 request_delay: float = 1.2,
                 max_retries: int = 4):
        self.username = username or os.environ.get("DHS_USER")
        self.password = password or os.environ.get("DHS_PASSWORD")
        self.cookie_str = cookie_str or os.environ.get("DHS_COOKIE")
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "brutos"
        self.extracted_dir = self.output_dir / "extraidos"
        self.request_delay = max(0.0, request_delay)
        self.max_retries = max(0, max_retries)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://dhsprogram.com/data/dataset_admin/download-manager.cfm"
        })
        self.is_authenticated = False
        self.active_project = None

    @staticmethod
    def is_retriable_status(status_code: int) -> bool:
        return status_code in {403, 429, 500, 502, 503, 504}

    def setup_session(self) -> bool:
        """Configura a sessão autenticada com cookies ou login."""
        # Se forneceu cookie string
        if self.cookie_str:
            for item in self.cookie_str.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    self.session.cookies.set(k, v)
            print("[INFO] Cookies de sessão configurados manualmente.")
            self.is_authenticated = True
            self._select_active_project()
            return True

        # Se forneceu usuário e senha
        if self.username and self.password:
            return self.login(self.username, self.password)

        return False

    def _extract_and_set_cf_cookies(self, url: str):
        """Extrai CFID e CFTOKEN da URL e salva nos cookies da sessão."""
        import urllib.parse
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        cfid = parsed.get("CFID", [""])[0]
        cftoken = parsed.get("CFTOKEN", [""])[0]
        if cfid and cftoken:
            self.session.cookies.set("CFID", cfid, domain="dhsprogram.com")
            self.session.cookies.set("CFTOKEN", cftoken, domain="dhsprogram.com")

    def _select_active_project(self) -> bool:
        """Identifica e seleciona o projeto DHS aprovado na sessão ativa."""
        try:
            from bs4 import BeautifulSoup
            r = self.session.get(DHS_INDEX_URL, timeout=15)
            self._extract_and_set_cf_cookies(r.url)

            soup = BeautifulSoup(r.text, "html.parser")
            proj_select = soup.find("select", attrs={"name": "proj_id"})
            if not proj_select:
                return False

            projects = []
            for opt in proj_select.find_all("option"):
                val = opt.get("value", "").strip()
                txt = opt.get_text(strip=True)
                if val and val != "0":
                    projects.append((val, txt))

            if not projects:
                print("[AVISO] Nenhum projeto de pesquisa encontrado na conta DHS.")
                return False

            # Seleciona o primeiro projeto aprovado disponível
            proj_id, proj_title = projects[0]
            r_post = self.session.post(DHS_INDEX_URL, data={"proj_id": proj_id}, timeout=15)
            self._extract_and_set_cf_cookies(r_post.url)
            self.active_project = proj_title
            print("[PROJETO] Projeto ativo selecionado no DHS.")
            return True
        except Exception as e:
            print(f"[AVISO] Não foi possível selecionar o projeto automaticamente: {e}")
            return False

    def login(self, username: str, password: str) -> bool:
        """Realiza autenticação no DHS Program via formulário POST e ativa o projeto."""
        print("[AUTH] Autenticando no DHS Program com as credenciais configuradas...")
        try:
            # 1. Obter cookies iniciais (JSESSIONID, CSRFTOKEN)
            r_init = self.session.get(DHS_LOGIN_URL, timeout=15)
            self._extract_and_set_cf_cookies(r_init.url)

            # 2. Submeter formulário de login
            login_data = {
                "Submitted": "1",
                "UserType": "2",
                "UserName": username,
                "UserPass": password,
                "submit": "Sign In"
            }
            resp = self.session.post(DHS_LOGIN_URL, data=login_data, timeout=20, allow_redirects=True)
            self._extract_and_set_cf_cookies(resp.url)

            if "login_main.cfm" in resp.url.lower():
                print("[ERRO] Falha no login do DHS: Usuário ou senha incorretos ou redirecionado para login.")
                return False

            print("[SUCESSO] Login realizado com sucesso no DHS Program!")
            self.is_authenticated = True

            # 3. Selecionar projeto ativo para habilitar downloads dos países aprovados
            self._select_active_project()
            return True
        except Exception as e:
            print(f"[ERRO] Falha na conexão de login: {e}")
            return False

    def prompt_credentials_if_needed(self):
        """Solicita credenciais interativamente se nenhuma foi informada."""
        if self.is_authenticated:
            return

        print("\n" + "=" * 70)
        print("  DHS PROGRAM - AUTENTICAÇÃO NECESSÁRIA")
        print("=" * 70)
        print("Os microdados do DHS Program exigem cadastro e projeto aprovado.")
        print("Escolha como deseja autenticar:")
        print(" 1) Informar e-mail e senha do DHS")
        print(" 2) Informar cookies da sua sessão aberta no navegador")
        print(" 3) Continuar sem login (testar URLs / verificar)")
        print("=" * 70)

        choice = input("Opção [1/2/3] (padrão 1): ").strip()
        if choice == "2":
            cookie = input("Cole a string de cookies (ex: CFID=...; CFTOKEN=...): ").strip()
            if cookie:
                self.cookie_str = cookie
                self.setup_session()
        elif choice == "3":
            print("[AVISO] Continuando sem autenticação. Downloads podem redirecionar para a página de login.")
        else:
            user = input("E-mail DHS: ").strip()
            if user:
                pwd = getpass.getpass("Senha DHS: ").strip()
                self.username = user
                self.password = pwd
                self.login(user, pwd)

    def download_file(self, item: Dict[str, str], extract: bool = False) -> Dict[str, str]:
        """
        Baixa um único dataset e o organiza no diretório correspondente.
        Verifica se é realmente um arquivo ZIP antes de salvar.
        """
        filename = item["filename"]
        url = item["url"]
        country_name = item["country_name"]
        category_folder = item["category_folder"]

        target_dir = self.raw_dir / country_name / category_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / filename

        # Se já existe e é um zip válido, pula
        if target_file.exists() and target_file.stat().st_size > 5000:
            if zipfile.is_zipfile(target_file):
                if extract:
                    self._extract_zip(target_file, country_name, category_folder, filename)
                return {"filename": filename, "status": "JA_EXISTE", "path": str(target_file)}

        temp_file = target_file.with_suffix(".tmp")
        for attempt in range(self.max_retries + 1):
            try:
                if attempt == 0 and self.request_delay:
                    time.sleep(self.request_delay)
                with self.session.get(url, stream=True, timeout=90, allow_redirects=True) as resp:
                    status_code = resp.status_code
                    if self.is_retriable_status(status_code):
                        if attempt < self.max_retries:
                            retry_after = resp.headers.get("Retry-After")
                            try:
                                wait_seconds = float(retry_after) if retry_after else 2 ** attempt
                            except ValueError:
                                wait_seconds = 2 ** attempt
                            time.sleep(wait_seconds)
                            continue
                        return {
                            "filename": filename,
                            "status": "BLOQUEADO_TAXA",
                            "error": f"HTTP {status_code} após {attempt + 1} tentativas; a execução pode ser retomada depois.",
                        }

                    if status_code >= 400:
                        return {
                            "filename": filename,
                            "status": "HTTP_ERROR",
                            "error": f"HTTP {status_code}: {resp.reason}",
                        }

                    content_type = resp.headers.get("Content-Type", "").lower()
                    final_url = resp.url.lower()
                    if "login_main" in final_url or "text/html" in content_type:
                        return {
                            "filename": filename,
                            "status": "AUTH_REQUIRED",
                            "error": "Acesso negado ou redirecionado para a página de login DHS.",
                        }

                    with open(temp_file, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)

                if not zipfile.is_zipfile(temp_file):
                    temp_file.unlink(missing_ok=True)
                    return {
                        "filename": filename,
                        "status": "INVALID_RESPONSE",
                        "error": "A resposta não é um ZIP válido.",
                    }

                actual_size = temp_file.stat().st_size
                temp_file.replace(target_file)
                if extract:
                    self._extract_zip(target_file, country_name, category_folder, filename)

                result = {"filename": filename, "status": "SUCESSO", "path": str(target_file), "size": actual_size}
                expected_size = item.get("expected_size")
                if expected_size and actual_size != int(expected_size):
                    result["warning"] = f"Tamanho recebido ({actual_size}) difere do catálogo DHS ({expected_size})."
                return result

            except requests.RequestException as exc:
                if attempt == self.max_retries:
                    return {"filename": filename, "status": "FALHA_REDE", "error": str(exc)}
                time.sleep(2 ** attempt)
            except OSError as exc:
                return {"filename": filename, "status": "FALHA_DISCO", "error": str(exc)}
            finally:
                temp_file.unlink(missing_ok=True)

        return {"filename": filename, "status": "FALHA", "error": "Tentativas esgotadas."}

    def _extract_zip(self, zip_path: Path, country: str, category: str, filename: str):
        """Extrai os arquivos .dta e documentação do zip."""
        extract_target = self.extracted_dir / country / category / zip_path.stem
        extract_target.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(extract_target)
        except Exception as e:
            print(f"[AVISO] Não foi possível extrair {filename}: {e}")

    def run(self,
        urls_file: str = "catalogo_datasets.csv",
            country_filter: Optional[List[str]] = None,
            recode_filter: Optional[List[str]] = None,
            survey_filter: Optional[List[str]] = None,
            limit: Optional[int] = None,
            extract: bool = False,
            max_workers: int = DEFAULT_WORKERS,
            use_api: bool = True):
        """Executa a rotina de download e organização com base nos filtros."""
        catalog = load_catalog(urls_file)
        print(f"[CATÁLOGO] Total de datasets disponíveis: {len(catalog)}")

        # Aplicar filtros
        filtered = catalog
        if country_filter:
            country_filter = [c.upper() for c in country_filter]
            filtered = [
                item for item in filtered
                if item["country_code"] in country_filter or item["country_name"].upper() in country_filter
            ]
            print(f"[FILTRO] Países {country_filter} -> {len(filtered)} datasets selecionados.")

        if recode_filter:
            recode_filter = [r.upper() for r in recode_filter]
            filtered = [item for item in filtered if item["recode_code"] in recode_filter]
            print(f"[FILTRO] Recodes {recode_filter} -> {len(filtered)} datasets selecionados.")

        if survey_filter:
            filtered = [item for item in filtered if item["surv_id"] in survey_filter]
            print(f"[FILTRO] Surveys {survey_filter} -> {len(filtered)} datasets selecionados.")

        if limit and limit > 0:
            filtered = filtered[:limit]
            print(f"[FILTRO] Limite máximo aplicado: {limit} datasets.")

        if not filtered:
            print("[AVISO] Nenhum dataset corresponde aos filtros informados.")
            return

        if use_api:
            print("[API] Validando tamanho e formato no catálogo público do DHS...")
            filtered = DHSApiClient().enrich(filtered)
            validated = sum(item["api_validation"] == "ENCONTRADO" for item in filtered)
            print(f"[API] {validated}/{len(filtered)} arquivos encontrados no catálogo público.")

        # Configurar sessão
        if not self.setup_session():
            self.prompt_credentials_if_needed()

        print("\n" + "=" * 70)
        print(f"  INICIANDO DOWNLOAD DE {len(filtered)} DATASETS")
        print(f"  Destino Bruto:     {self.raw_dir.resolve()}")
        if extract:
            print(f"  Destino Extraído:  {self.extracted_dir.resolve()}")
        print(f"  Downloads simultâneos: {max_workers}")
        print(f"  Pausa por download: {self.request_delay:.1f}s")
        print("=" * 70 + "\n")

        results = []
        counts = {
            "SUCESSO": 0,
            "JA_EXISTE": 0,
            "AUTH_REQUIRED": 0,
            "BLOQUEADO_TAXA": 0,
            "HTTP_ERROR": 0,
            "INVALID_RESPONSE": 0,
            "FALHA_REDE": 0,
            "FALHA_DISCO": 0,
            "FALHA": 0,
        }

        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
            future_to_item = {
                executor.submit(self.download_file, item, extract): item
                for item in filtered
            }

            with tqdm(total=len(filtered), desc="Progresso", unit="dataset") as pbar:
                for future in as_completed(future_to_item):
                    try:
                        res = future.result()
                    except Exception as exc:
                        res = {"filename": future_to_item[future]["filename"], "status": "FALHA", "error": str(exc)}
                    results.append(res)
                    status = res.get("status", "FALHA")
                    counts[status] = counts.get(status, 0) + 1
                    pbar.set_postfix({
                        "Baixados": counts["SUCESSO"],
                        "Existentes": counts["JA_EXISTE"],
                        "Auth/Login": counts["AUTH_REQUIRED"],
                        "Bloqueados": counts["BLOQUEADO_TAXA"],
                    })
                    pbar.update(1)

        print("\n" + "=" * 70)
        print("  RESUMO DO PROCESSO")
        print("=" * 70)
        print(f"  - Total processado:    {len(filtered)}")
        print(f"  - Baixados agora:      {counts['SUCESSO']}")
        print(f"  - Já existiam:         {counts['JA_EXISTE']}")
        print(f"  - Requer login DHS:    {counts['AUTH_REQUIRED']}")
        print(f"  - Bloqueados por taxa: {counts['BLOQUEADO_TAXA']}")
        print(f"  - Falhas de rede:      {counts['FALHA_REDE']}")
        print(f"  - Outros erros:        {sum(value for key, value in counts.items() if key in {'HTTP_ERROR', 'INVALID_RESPONSE', 'FALHA_DISCO', 'FALHA'})}")
        print("=" * 70)

        if counts["AUTH_REQUIRED"] > 0:
            print("\n[ATENÇÃO] Alguns arquivos não puderam ser baixados porque o DHS Program exige login.")
            print("Para baixar todos com sucesso:")
            print("1. Cadastre-se gratuitamente em https://dhsprogram.com e solicite acesso aos dados da África.")
            print("2. Execute o script passando suas credenciais:")
            print("   python baixar_datasets.py --username SEU_EMAIL --password SUA_SENHA")
            print("   ou crie um arquivo .env com:")
            print("   DHS_USER=seu_email@dominio.com")
            print("   DHS_PASSWORD=sua_senha")

        # Salvar relatório
        report_file = self.output_dir / f"relatorio_download_{datetime.now():%Y%m%d_%H%M%S}.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        import json
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "resumo": counts,
                "api_validacao_ativada": use_api,
                "detalhes": results,
            }, f, indent=2, ensure_ascii=False)
        print(f"\nRelatório salvo em: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Baixa e organiza os dados do DHS Program para o projeto de Banco de Dados (DCC011)."
    )
    parser.add_argument(
        "--urls-file",
        default="catalogo_datasets.csv",
        help="Caminho do catálogo CSV exportado ou arquivo de URLs.",
    )
    parser.add_argument("--country", "-c", help="Códigos dos países separados por vírgula (ex: AO,MZ,KE,GH).")
    parser.add_argument("--recode", "-r", help="Tipos de recode separados por vírgula (ex: IR para Saúde da Mulher, BR para Nascimentos).")
    parser.add_argument("--survey", "-s", help="IDs de surveys separados por vírgula.")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Limite de arquivos a baixar.")
    parser.add_argument("--extract", "-x", action="store_true", help="Extrai os arquivos .zip automaticamente.")
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR, help="Pasta de saída.")
    parser.add_argument("--workers", "-w", type=int, default=DHSDownloader.DEFAULT_WORKERS,
                        help="Número de downloads simultâneos (padrão: 1, recomendado para evitar 403).")
    parser.add_argument("--delay", type=float, default=1.2,
                        help="Pausa em segundos entre downloads (padrão: 1.2).")
    parser.add_argument("--retries", type=int, default=4,
                        help="Tentativas adicionais para 403, 429 e erros temporários (padrão: 4).")
    parser.add_argument("--skip-api", action="store_true",
                        help="Não consulta os metadados públicos da API DHS antes de baixar.")
    parser.add_argument("--username", "-u", default=None, help="Usuário/E-mail do DHS Program.")
    parser.add_argument("--password", "-p", default=None, help="Senha do DHS Program.")
    parser.add_argument("--cookie", default=None, help="Cookie de sessão do DHS Program.")
    parser.add_argument("--women-health-only", action="store_true",
                        help="Filtra apenas dados de Saúde da Mulher (Recode IR - pontuação extra no trabalho!).")

    args = parser.parse_args()

    # Filtro especial saúde da mulher
    recode_filter = None
    if args.women_health_only:
        recode_filter = ["IR"]
    elif args.recode:
        recode_filter = [r.strip() for r in args.recode.split(",")]

    country_filter = [c.strip() for c in args.country.split(",")] if args.country else None
    survey_filter = [s.strip() for s in args.survey.split(",")] if args.survey else None

    downloader = DHSDownloader(
        username=args.username,
        password=args.password,
        cookie_str=args.cookie,
        output_dir=args.output_dir,
        request_delay=args.delay,
        max_retries=args.retries,
    )

    downloader.run(
        urls_file=args.urls_file,
        country_filter=country_filter,
        recode_filter=recode_filter,
        survey_filter=survey_filter,
        limit=args.limit,
        extract=args.extract,
        max_workers=args.workers,
        use_api=not args.skip_api,
    )


if __name__ == "__main__":
    main()
