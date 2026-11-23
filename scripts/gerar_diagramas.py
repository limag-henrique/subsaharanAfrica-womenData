"""Gera o modelo relacional Mermaid a partir do DDL, preservando o ER original."""
import ast
import json
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RELACOES = [
    ('Pais','Levantamento','realiza'), ('Levantamento','Domicilio','amostra'),
    ('Domicilio','Morador','abriga'), ('Domicilio','Mulher','reside'),
    ('Domicilio','Parceiro','reside'), ('Mulher','Entrevista','responde'),
    ('Mulher','Nascimento','tem_parto'), ('Nascimento','Crianca','origina'),
    ('Mulher','Conhecimento_Metodo','informa'), ('Metodo','Conhecimento_Metodo','classifica'),
    ('Crianca','Crianca_Vacina','recebe'), ('Vacina_Remedio','Crianca_Vacina','identifica'),
]


def esquema():
    nb = json.loads((RAIZ / 'Saúde da Mulher na África Subsaariana.ipynb').read_text(encoding='utf-8'))
    for celula in nb['cells']:
        if celula['cell_type'] != 'code':
            continue
        for comando in ast.parse(''.join(celula['source'])).body:
            if isinstance(comando, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'DDL' for t in comando.targets):
                banco = sqlite3.connect(':memory:')
                banco.executescript(comando.value.value)
                return banco
    raise ValueError('DDL ausente.')


def main():
    banco = esquema()
    tabelas = [r[0] for r in banco.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    mermaid = ['---', 'config:', '  theme: default', '  look: classic', '  layout: dagre', '---', 'erDiagram']
    for tabela in tabelas:
        mermaid.append(f'    {tabela} {{')
        fks = {r[3] for r in banco.execute(f'PRAGMA foreign_key_list({tabela})')}
        unicas = set()
        for indice in banco.execute(f'PRAGMA index_list({tabela})').fetchall():
            if indice[2] and indice[3] != 'pk':
                colunas = [r[2] for r in banco.execute(f'PRAGMA index_info("{indice[1]}")')]
                if len(colunas) == 1:
                    unicas.add(colunas[0])
        for _, nome, tipo, _, _, pk in banco.execute(f'PRAGMA table_info({tabela})'):
            chaves = ','.join((['PK'] if pk else []) + (['FK'] if nome in fks else []) + (['UK'] if nome in unicas else []))
            mermaid.append(f'        {tipo} {nome}' + (' ' + chaves if chaves else ''))
        mermaid.append('    }')
    for pai, filho, nome in RELACOES:
        chave = {r[1] for r in banco.execute(f'PRAGMA table_info({filho})') if r[5]}
        identificadora = any(r[2] == pai and r[3] in chave for r in banco.execute(f'PRAGMA foreign_key_list({filho})'))
        linha = '--' if identificadora else '..'
        cardinalidade = '||' + linha + ('o|' if filho == 'Entrevista' else 'o{')
        mermaid.append(f'    {pai} {cardinalidade} {filho} : {nome}')
    (RAIZ/'docs/Diagrama Relacional.mmd').write_text('\n'.join(mermaid)+'\n',encoding='utf-8')
    banco.close()
    print('Modelo Mermaid atualizado; ER original preservado.')


if __name__ == '__main__':
    main()
