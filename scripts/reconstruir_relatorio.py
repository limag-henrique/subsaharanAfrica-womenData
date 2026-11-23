"""Reconstrói o banco final dos CSVs e suplementos Stata em um destino novo."""
import argparse
import ast
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino', type=Path, required=True)
    parser.add_argument('--extraidos', type=Path, required=True)
    args = parser.parse_args()
    destino = args.destino.resolve()
    preparacao = destino.with_name(destino.stem + '_partos.db')
    if destino.exists() or preparacao.exists():
        parser.error('Os destinos final e de preparação devem ser novos.')
    manifesto = json.loads((RAIZ / 'docs/manifesto_contracepcao.json').read_text(encoding='utf-8'))
    suplementos = []
    for item in manifesto:
        encontrados = [p for p in args.extraidos.rglob('*') if p.is_file() and p.name.lower() == item['arquivo_origem'].lower()]
        if len(encontrados) != 1:
            parser.error(f"Esperado um arquivo {item['arquivo_origem']}; encontrados {len(encontrados)}.")
        suplementos.append(dict(item, caminho_origem=str(encontrados[0].resolve())))
    # Reutiliza as mesmas definições de carga do notebook, sem executar gráficos/consultas.
    nb = json.loads((RAIZ / 'Saúde da Mulher na África Subsaariana.ipynb').read_text(encoding='utf-8'))
    contexto = {}
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        texto = ''.join(cell['source'])
        arvore = ast.parse(texto)
        if any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DDL' for t in n.targets) for n in arvore.body):
            exec(compile(arvore, '<DDL notebook>', 'exec'), contexto)
        if any(isinstance(n, ast.FunctionDef) and n.name == 'preparar_banco' for n in arvore.body):
            exec(compile(arvore, '<carga notebook>', 'exec'), contexto)
    destino.parent.mkdir(parents=True, exist_ok=True)
    contexto['preparar_banco'](RAIZ / 'dados/relevantes', preparacao, suplementos)
    contexto['normalizar_datas'](preparacao, destino, contexto['DDL'])
    print(f'Banco final reconstruído: {destino}')


if __name__ == '__main__':
    main()
