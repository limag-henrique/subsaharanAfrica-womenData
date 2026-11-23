"""Modelo de partos e filhos do notebook principal, sem modificar a base anterior.

BIDX segue a ordem inversa dos filhos; B0 segue a ordem dentro do parto
múltiplo. Assim, BIDX + B0 - 1 identifica o primeiro irmão desse parto no
histórico. A data CMC também deve coincidir. Sem B0/data válida não há fusão.
"""

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from database_python.relatorio_notebook import DDL_NORMALIZADO, construir_banco


TABELAS_PARTOS = """
CREATE TABLE Nascimento(
  id TEXT PRIMARY KEY, mulher_id TEXT NOT NULL REFERENCES Mulher(id),
  ano INTEGER, mes INTEGER, data_cmc INTEGER,
  consultas_prenatal_codigo INTEGER, local_parto_codigo INTEGER, cesarea_codigo INTEGER,
  assistencia_medico_codigo INTEGER, assistencia_m3b_codigo INTEGER,
  campos_conflitantes TEXT NOT NULL DEFAULT '');
CREATE TABLE Crianca(
  id TEXT PRIMARY KEY, nascimento_id TEXT NOT NULL REFERENCES Nascimento(id),
  indice INTEGER NOT NULL CHECK(indice>=1), sexo INTEGER CHECK(sexo IN(1,2)),
  vivo INTEGER CHECK(vivo IN(0,1)), idade_anos INTEGER,
  diarreia_codigo INTEGER, cartao_vacina_codigo INTEGER,
  ordem_multiplo INTEGER CHECK(ordem_multiplo BETWEEN 0 AND 7),
  tem_registro_kr INTEGER NOT NULL CHECK(tem_registro_kr IN(0,1)),
  origem TEXT NOT NULL CHECK(origem IN('BR','KR_sem_BR')),
  UNIQUE(nascimento_id,indice));
CREATE TABLE Vacina_Remedio(
  id INTEGER PRIMARY KEY, codigo TEXT NOT NULL UNIQUE, nome TEXT NOT NULL UNIQUE);
CREATE TABLE Crianca_Vacina(
  crianca_id TEXT NOT NULL REFERENCES Crianca(id),
  vacina_id INTEGER NOT NULL REFERENCES Vacina_Remedio(id),
  status_codigo INTEGER NOT NULL CHECK(status_codigo BETWEEN 0 AND 9),
  PRIMARY KEY(crianca_id,vacina_id)) WITHOUT ROWID;
"""
DDL_PARTOS = (
    DDL_NORMALIZADO[:DDL_NORMALIZADO.index("CREATE TABLE Nascimento(")]
    + TABELAS_PARTOS
    + DDL_NORMALIZADO[DDL_NORMALIZADO.index("CREATE TABLE Morador("):]
)


def migrar_banco_partos(legado, origem, destino, ddl=DDL_PARTOS):
    """Publica uma cópia migrada apenas após validar filhos, vacinas e FKs.

    `legado` é a base normalizada por filho; `origem` contém BR e KR com B0.
    Ambos são abertos somente para leitura e nunca são substituídos.
    """
    legado, origem, destino = (Path(p).resolve() for p in (legado, origem, destino))
    if destino in (legado, origem) or destino.exists():
        raise ValueError("A migração requer um destino novo, diferente das fontes.")
    temporario = destino.with_name(f".partos_{uuid4().hex}.db")
    try:
        with closing(sqlite3.connect(legado.as_uri() + "?mode=ro", uri=True)) as fonte:
            with closing(sqlite3.connect(temporario.as_uri(), uri=True)) as banco:
                fonte.backup(banco)
                banco.execute("PRAGMA foreign_keys=OFF")
                banco.execute("ATTACH DATABASE ? AS bruto", (origem.as_uri() + "?mode=ro",))
                banco.execute("BEGIN")
                for tabela in ("Nascimento", "Crianca", "Crianca_Vacina"):
                    banco.execute(f'ALTER TABLE {tabela} RENAME TO _{tabela}_anterior')
                # Apenas as três tabelas alteradas: as demais relações e índices ficam intactos.
                for comando in ddl.split(";"):
                    if comando.strip().startswith(("CREATE TABLE Nascimento(",
                                                   "CREATE TABLE Crianca(",
                                                   "CREATE TABLE Crianca_Vacina(")):
                        banco.execute(comando)
                banco.execute("CREATE TEMP TABLE ordem_filho(id TEXT PRIMARY KEY, b0 INTEGER)")
                for tabela in ("Nascimento", "Crianca"):
                    colunas = {r[1] for r in banco.execute(f"PRAGMA bruto.table_info({tabela})")}
                    if "b0" not in colunas:
                        raise ValueError(f"B0 ausente em {tabela}; não é seguro agrupar partos.")
                    banco.execute(f"""INSERT OR IGNORE INTO ordem_filho
                        SELECT levantamento_id||'|'||CAST(v001 AS INTEGER)||'|'||
                               CAST(v002 AS INTEGER)||'|'||CAST(v003 AS INTEGER)||'|'||
                               CAST(bidx AS INTEGER), b0 FROM bruto.{tabela}""")
                banco.execute("""CREATE TEMP TABLE vinculo_parto AS
                    SELECT n.id AS crianca_id, o.b0,
                        n.mulher_id || '|parto|' ||
                        CASE WHEN o.b0 BETWEEN 1 AND 7 AND n.data_cmc > 0
                             THEN 'multiplo|' || (n.indice + o.b0 - 1) || '|' || n.data_cmc
                             ELSE 'individual|' || n.indice END AS nascimento_id
                    FROM _Nascimento_anterior n
                    LEFT JOIN ordem_filho o ON o.id = n.id""")
                banco.execute("CREATE UNIQUE INDEX idx_vinculo_crianca ON vinculo_parto(crianca_id)")
                campos = ["ano", "mes", "data_cmc", "consultas_prenatal_codigo",
                          "local_parto_codigo", "cesarea_codigo", "assistencia_medico_codigo",
                          "assistencia_m3b_codigo"]
                valores = ",".join(
                    f"CASE WHEN COUNT(DISTINCT n.{campo}) <= 1 THEN MAX(n.{campo}) END"
                    for campo in campos
                )
                conflitos = " || ".join(
                    f"CASE WHEN COUNT(DISTINCT n.{campo}) > 1 THEN '{campo},' ELSE '' END"
                    for campo in campos
                )
                banco.execute(f"""INSERT INTO Nascimento
                    SELECT v.nascimento_id, n.mulher_id, {valores}, RTRIM({conflitos}, ',')
                    FROM _Nascimento_anterior n JOIN vinculo_parto v ON v.crianca_id=n.id
                    GROUP BY v.nascimento_id, n.mulher_id""")
                # O notebook omite variáveis KR que não usa; respeitar o DDL fornecido.
                colunas_crianca = {r[1] for r in banco.execute('PRAGMA table_info(Crianca)')}
                extras_kr = [nome for nome in ('diarreia_codigo', 'cartao_vacina_codigo')
                             if nome in colunas_crianca]
                projecao_kr = ''.join(f'k.{nome}, ' for nome in extras_kr)
                banco.execute(f"""INSERT INTO Crianca
                    SELECT n.id, v.nascimento_id, n.indice, n.sexo, n.vivo,
                           k.idade_anos, {projecao_kr}
                           CASE WHEN v.b0 BETWEEN 0 AND 7 THEN v.b0 END,
                           k.nascimento_id IS NOT NULL, n.origem
                    FROM _Nascimento_anterior n JOIN vinculo_parto v ON v.crianca_id=n.id
                    LEFT JOIN _Crianca_anterior k ON k.nascimento_id=n.id""")
                banco.execute("""INSERT INTO Crianca_Vacina
                    SELECT nascimento_id, vacina_id, status_codigo FROM _Crianca_Vacina_anterior""")
                for consulta, mensagem in [
                    ("SELECT id,sexo,vivo,indice,origem FROM _Nascimento_anterior EXCEPT "
                     "SELECT id,sexo,vivo,indice,origem FROM Crianca", "Dados individuais alterados"),
                    ("SELECT nascimento_id,idade_anos" + ''.join(',' + nome for nome in extras_kr) +
                     " FROM _Crianca_anterior EXCEPT SELECT id,idade_anos" +
                     ''.join(',' + nome for nome in extras_kr) + " FROM Crianca WHERE tem_registro_kr=1",
                     "Dados KR alterados"),
                    ("SELECT * FROM _Crianca_Vacina_anterior EXCEPT SELECT * FROM Crianca_Vacina",
                     "Vacinação alterada"),
                ]:
                    if banco.execute(consulta).fetchone():
                        raise ValueError(mensagem)
                anterior = banco.execute("SELECT COUNT(*) FROM _Nascimento_anterior").fetchone()[0]
                if banco.execute("SELECT COUNT(*) FROM Crianca").fetchone()[0] != anterior:
                    raise ValueError("Perda ou duplicação de filhos na migração")
                for tabela in ("Crianca_Vacina", "Crianca", "Nascimento"):
                    banco.execute(f"DROP TABLE _{tabela}_anterior")
                banco.execute("CREATE INDEX idx_crianca_nascimento ON Crianca(nascimento_id)")
                banco.execute("CREATE INDEX idx_nascimento_mulher ON Nascimento(mulher_id)")
                if banco.execute("PRAGMA foreign_key_check").fetchone():
                    raise ValueError("Vínculos inválidos após a migração")
                if banco.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Banco migrado sem integridade")
                banco.commit()
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)
    return destino


def construir_banco_partos(origem, destino, suplementos=(), ddl=DDL_PARTOS):
    """Reconstrói a partir dos recodes e aplica a separação parto–filho."""
    destino = Path(destino).resolve()
    if destino.exists():
        raise ValueError("Escolha um destino novo para a reconstrução.")
    legado = destino.with_name(f".filhos_{uuid4().hex}.db")
    try:
        construir_banco(origem, legado, suplementos)
        return migrar_banco_partos(legado, origem, destino, ddl)
    finally:
        legado.unlink(missing_ok=True)
