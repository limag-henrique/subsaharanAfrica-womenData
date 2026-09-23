"""
Servidor Flask para o Visualizador Interativo do Banco de Dados DHS
Saude da Mulher na Africa Subsaariana
"""
import os
import sys
import json
import sqlite3
import math
from flask import Flask, jsonify, request, send_from_directory

# Adiciona o diretorio ao path para importar label_maps
sys.path.insert(0, os.path.dirname(__file__))
import label_maps as lm

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'saude_mulher_dhs.db')
STATIC_DIR = os.path.dirname(__file__)

app = Flask(__name__, static_folder=STATIC_DIR)

PAGE_SIZE = 50  # registros por pagina


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'db_viewer.html')


@app.route('/api/tables')
def list_tables():
    """Lista todas as tabelas do banco de dados com contagem de linhas."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    result = []
    for t in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{t}"')
            count = cursor.fetchone()[0]
        except:
            count = 0
        result.append({"name": t, "count": count})
    conn.close()
    return jsonify(result)


@app.route('/api/columns')
def get_columns():
    """Retorna colunas de uma tabela com rotulos legiveis."""
    table = request.args.get('table', '')
    if not table:
        return jsonify({"error": "Tabela nao especificada"}), 400
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f'PRAGMA table_info("{table}")')
        cols = cursor.fetchall()
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500
    conn.close()
    coded = lm.get_coded_columns()
    result = []
    for c in cols:
        col_code = c[1]
        result.append({
            "code": col_code,
            "label": lm.get_column_label(table, col_code),
            "has_value_map": col_code in coded,
        })
    return jsonify(result)


@app.route('/api/data')
def get_data():
    """Retorna dados paginados com valores traduzidos."""
    table = request.args.get('table', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', PAGE_SIZE))
    search = request.args.get('search', '').strip()
    filter_country = request.args.get('pais_codigo', '').strip()
    filter_phase = request.args.get('fase', '').strip()
    translate = request.args.get('translate', 'true').lower() == 'true'
    show_raw = request.args.get('show_raw', 'false').lower() == 'true'

    if not table:
        return jsonify({"error": "Tabela nao especificada"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Obter colunas
    try:
        cursor.execute(f'PRAGMA table_info("{table}")')
        cols_info = cursor.fetchall()
        col_names = [c[1] for c in cols_info]
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

    # Montar WHERE
    conditions = []
    params = []
    if filter_country:
        conditions.append('"pais_codigo" = ?')
        params.append(filter_country)
    if filter_phase:
        conditions.append('"fase" = ?')
        params.append(filter_phase)
    if search and len(col_names) > 0:
        search_cols = [c for c in col_names if c in ('pais_nome', 'caseid', 'hhid', 'mcaseid', 'whhid', 'pais_codigo')]
        if search_cols:
            like_conds = [f'CAST("{c}" AS TEXT) LIKE ?' for c in search_cols]
            conditions.append('(' + ' OR '.join(like_conds) + ')')
            params.extend([f'%{search}%'] * len(search_cols))

    where_clause = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    # Contar total
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table}" {where_clause}', params)
        total = cursor.fetchone()[0]
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

    # Paginar
    offset = (page - 1) * per_page
    try:
        cursor.execute(
            f'SELECT * FROM "{table}" {where_clause} LIMIT ? OFFSET ?',
            params + [per_page, offset]
        )
        rows = cursor.fetchall()
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

    conn.close()

    coded = lm.get_coded_columns()
    result_rows = []
    for row in rows:
        row_dict = {}
        for col, val in zip(col_names, row):
            if translate and col in coded:
                label_val = lm.get_value_label(col, val)
                if show_raw and label_val != val:
                    row_dict[col] = f"{label_val} [{val}]"
                else:
                    row_dict[col] = label_val
            else:
                row_dict[col] = val
        result_rows.append(row_dict)

    # Construir labels de colunas
    col_labels = {c: lm.get_column_label(table, c) for c in col_names}

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page) if per_page > 0 else 0,
        "columns": col_names,
        "column_labels": col_labels,
        "rows": result_rows,
    })


@app.route('/api/countries')
def get_countries():
    """Retorna lista de paises disponíveis."""
    table = request.args.get('table', 'Mulher')
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT DISTINCT pais_codigo, pais_nome FROM "{table}" ORDER BY pais_nome')
        rows = cursor.fetchall()
        result = [{"codigo": r[0], "nome": r[1]} for r in rows]
    except:
        try:
            cursor.execute('SELECT pais_codigo, nome_pais FROM "Pais" ORDER BY nome_pais')
            rows = cursor.fetchall()
            result = [{"codigo": r[0], "nome": r[1]} for r in rows]
        except:
            result = []
    conn.close()
    return jsonify(result)


@app.route('/api/phases')
def get_phases():
    """Retorna fases DHS disponíveis."""
    table = request.args.get('table', 'Mulher')
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT DISTINCT fase FROM "{table}" ORDER BY fase')
        rows = cursor.fetchall()
        result = [r[0] for r in rows]
    except:
        result = []
    conn.close()
    return jsonify(result)


if __name__ == '__main__':
    print("=" * 60)
    print("  Visualizador DHS - Saude da Mulher na Africa Subsaariana")
    print("=" * 60)
    print(f"  Banco de dados: {DB_PATH}")
    print(f"  Acesse: http://localhost:5050")
    print("  Pressione Ctrl+C para parar")
    print("=" * 60)
    app.run(debug=False, port=5050, host='0.0.0.0')
