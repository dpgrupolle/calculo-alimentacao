"""Repositório de Funcionários (cadastro Sankhya)."""
from __future__ import annotations
from typing import List, Optional
from src.banco.conexao import obter_conexao, transacao


def listar(apenas_ativos: bool = False, busca: str = "", empresa: str = "") -> List[dict]:
    sql = "SELECT * FROM funcionario WHERE 1=1"
    params: list = []
    if apenas_ativos:
        sql += " AND ativo = 1"
    if empresa:
        sql += " AND empresa = ?"; params.append(empresa)
    if busca:
        sql += " AND (LOWER(nome) LIKE ? OR codigo LIKE ? OR cpf LIKE ?)"
        t = f"%{busca.lower()}%"
        params += [t, f"%{busca}%", f"%{busca}%"]
    sql += " ORDER BY nome;"
    return obter_conexao().execute(sql, params).fetchall()


def contar(apenas_ativos: bool = True, empresa: str = "") -> int:
    sql = "SELECT COUNT(*) FROM funcionario WHERE 1=1"
    params = []
    if apenas_ativos: sql += " AND ativo = 1"
    if empresa: sql += " AND empresa = ?"; params.append(empresa)
    return int(obter_conexao().execute(sql, params).fetchone()[0])


def buscar_por_codigo(codigo: str) -> Optional[dict]:
    cur = obter_conexao().execute("SELECT * FROM funcionario WHERE codigo = ?;", (str(codigo),))
    return cur.fetchone()


def upsert_em_lote(funcionarios: List[dict]) -> dict:
    """Insere/atualiza pelo 'codigo' em lote (poucas idas ao banco). Retorna {inseridos, atualizados}."""
    if not funcionarios:
        return {"inseridos": 0, "atualizados": 0}
    conn = obter_conexao()
    existentes = {str(r["codigo"]) for r in conn.execute("SELECT codigo FROM funcionario;").fetchall()}
    novos, atualiza = [], []
    vistos = set()
    for f in funcionarios:
        cod = str(f.get("codigo", "")).strip()
        if not cod or cod in vistos:
            continue
        vistos.add(cod)
        if cod in existentes:
            atualiza.append((f.get("matricula"), f.get("nome"), f.get("cargo"), f.get("departamento"),
                             f.get("empresa") or "PISA", f.get("cpf"), f.get("faixa_alim"),
                             f.get("carga_horaria"), cod))
        else:
            novos.append((cod, f.get("matricula"), f.get("nome"), f.get("cargo"), f.get("departamento"),
                          f.get("empresa") or "PISA", f.get("cpf"), f.get("faixa_alim"), f.get("carga_horaria")))
    with transacao() as conn:
        if novos:
            conn.executemany(
                "INSERT INTO funcionario (codigo, matricula, nome, cargo, departamento, empresa, cpf, faixa_alim, carga_horaria) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", novos)
        if atualiza:
            conn.executemany(
                "UPDATE funcionario SET matricula=?, nome=?, cargo=?, departamento=?, empresa=?, cpf=?, faixa_alim=?, "
                "carga_horaria=?, ativo=1, atualizado_em=datetime('now') WHERE codigo=?;", atualiza)
    return {"inseridos": len(novos), "atualizados": len(atualiza)}


def todos_para_calculo(empresa: str = "") -> List[dict]:
    """Lista enxuta para o motor de cálculo (opcionalmente só de uma empresa)."""
    sql = ("SELECT codigo, matricula, nome, cargo, departamento, empresa, cpf, faixa_alim, carga_horaria "
           "FROM funcionario WHERE ativo = 1")
    params = []
    if empresa:
        sql += " AND empresa = ?"; params.append(empresa)
    rows = obter_conexao().execute(sql + ";", params).fetchall()
    return [dict(r) for r in rows]


def empresas_distintas() -> List[str]:
    rows = obter_conexao().execute(
        "SELECT DISTINCT empresa FROM funcionario WHERE empresa IS NOT NULL AND empresa<>'' ORDER BY empresa;").fetchall()
    return [r["empresa"] for r in rows]
