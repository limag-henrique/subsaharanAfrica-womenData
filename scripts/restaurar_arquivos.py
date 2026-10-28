"""Restaura os arquivos gzip particionados, conferindo SHA-256 (Python 3)."""
import gzip
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


def main():
    raiz = Path(__file__).resolve().parents[1]
    manifesto = json.loads((raiz / "arquivos_compactados/manifesto.json").read_text(encoding="utf-8"))
    for item in manifesto:
        destino = raiz / item["arquivo"]
        if destino.exists():
            with destino.open("rb") as origem:
                if hashlib.file_digest(origem, "sha256").hexdigest() == item["sha256"]:
                    print(f"Já restaurado: {item['arquivo']}")
                    continue
            raise SystemExit(f"Arquivo existente diferente; mova-o antes de restaurar: {destino}")
        destino.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile() as compactado:
            for parte in item["partes"]:
                caminho = raiz / "arquivos_compactados" / parte["nome"]
                with caminho.open("rb") as origem:
                    if hashlib.file_digest(origem, "sha256").hexdigest() != parte["sha256"]:
                        raise SystemExit(f"Parte corrompida: {caminho}")
                    origem.seek(0)
                    shutil.copyfileobj(origem, compactado)
            compactado.seek(0)
            with tempfile.NamedTemporaryFile(dir=destino.parent, delete=False) as saida:
                temporario = Path(saida.name)
                try:
                    with gzip.GzipFile(fileobj=compactado, mode="rb") as origem:
                        shutil.copyfileobj(origem, saida)
                except BaseException:
                    saida.close()
                    temporario.unlink(missing_ok=True)
                    raise
            try:
                with temporario.open("rb") as origem:
                    if hashlib.file_digest(origem, "sha256").hexdigest() != item["sha256"]:
                        raise SystemExit(f"Conteúdo restaurado inválido: {destino}")
                temporario.replace(destino)
            finally:
                temporario.unlink(missing_ok=True)
        print(f"Restaurado: {item['arquivo']}")


if __name__ == "__main__":
    main()
