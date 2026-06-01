"""
Schema do banco — Gestão de Benefícios DP/RH (modelo real).

Base (esqueleto): schema_versao, usuario, parametros_sistema, log_auditoria.
Negócio:
  - tabela_beneficio   : faixa de alimentação (1–13) → valor do prêmio (seed).
  - funcionario        : cadastro (codigo Sankhya, cpf, faixa_alim, carga_horaria).
  - processo           : fechamento mensal.
  - upload_planilha    : envios (FUNCIONARIOS / FALTAS / ATESTADOS).
  - falta_item         : faltas/atrasos consolidados por funcionário + flag incluir.
  - atestado_item      : atestados consolidados por funcionário (automático).
  - resultado_beneficio: resultado final por funcionário.
  - sodexo_modelo      : planilha-base da operadora guardada (Opção C).
"""
from __future__ import annotations
from typing import List

MIGRATIONS: List[str] = []

# 001 — base do esqueleto
MIGRATIONS.append("""
CREATE TABLE IF NOT EXISTS schema_versao (
    versao INTEGER PRIMARY KEY,
    aplicada_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK(perfil IN ('GESTAO_RH','ANALISTA_RH','DIRETORIA')),
    ativo INTEGER NOT NULL DEFAULT 1,
    deve_trocar_senha INTEGER NOT NULL DEFAULT 0,
    chave_aprovacao TEXT,
    aprovado INTEGER NOT NULL DEFAULT 0,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    ultimo_login TEXT
);
CREATE INDEX IF NOT EXISTS idx_usuario_email ON usuario(email);
CREATE TABLE IF NOT EXISTS parametros_sistema (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS log_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuario(id),
    usuario_nome_snapshot TEXT,
    acao TEXT NOT NULL,
    entidade TEXT, entidade_id INTEGER, detalhes TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
""")

# 002 — negócio
MIGRATIONS.append("""
CREATE TABLE IF NOT EXISTS tabela_beneficio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    valor_premio REAL NOT NULL DEFAULT 0,
    ativo INTEGER NOT NULL DEFAULT 1,
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS funcionario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,         -- Código do Sankhya (chave de ligação)
    matricula TEXT,
    nome TEXT NOT NULL,
    cargo TEXT,
    departamento TEXT,
    empresa TEXT NOT NULL DEFAULT 'PISA',
    cpf TEXT,
    faixa_alim INTEGER,                  -- 1–13
    carga_horaria TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_func_codigo ON funcionario(codigo);
CREATE INDEX IF NOT EXISTS idx_func_cpf ON funcionario(cpf);

CREATE TABLE IF NOT EXISTS processo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes_referencia TEXT NOT NULL,
    descricao TEXT,
    empresa TEXT NOT NULL DEFAULT 'PISA',
    status TEXT NOT NULL DEFAULT 'EM_ANDAMENTO' CHECK(status IN ('EM_ANDAMENTO','FINALIZADO')),
    total_funcionarios INTEGER NOT NULL DEFAULT 0,
    valor_total_premios REAL NOT NULL DEFAULT 0,
    valor_total_descontos REAL NOT NULL DEFAULT 0,
    valor_total_liquido REAL NOT NULL DEFAULT 0,
    usuario_id INTEGER REFERENCES usuario(id),
    usuario_nome_snapshot TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    finalizado_em TEXT
);
CREATE INDEX IF NOT EXISTS idx_processo_status ON processo(status);

CREATE TABLE IF NOT EXISTS upload_planilha (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK(tipo IN ('FUNCIONARIOS','FALTAS','ATESTADOS','FERIAS')),
    nome_arquivo TEXT NOT NULL,
    hash_arquivo TEXT,
    total_linhas INTEGER NOT NULL DEFAULT 0,
    usuario_id INTEGER REFERENCES usuario(id),
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(processo_id, tipo)
);

CREATE TABLE IF NOT EXISTS falta_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
    codigo TEXT,
    cpf TEXT,
    nome TEXT,
    atraso_min REAL NOT NULL DEFAULT 0,
    faltas_dias REAL NOT NULL DEFAULT 0,
    incluir INTEGER NOT NULL DEFAULT 1,   -- seleção manual (marca/desmarca)
    UNIQUE(processo_id, codigo)
);
CREATE INDEX IF NOT EXISTS idx_falta_proc ON falta_item(processo_id);

CREATE TABLE IF NOT EXISTS atestado_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
    codigo TEXT,
    matricula_pontotel TEXT,
    nome TEXT,
    dias REAL NOT NULL DEFAULT 0,
    indeterminado INTEGER NOT NULL DEFAULT 0,
    tipos TEXT,
    UNIQUE(processo_id, codigo)
);
CREATE INDEX IF NOT EXISTS idx_atest_proc ON atestado_item(processo_id);

CREATE TABLE IF NOT EXISTS ferias_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
    codigo TEXT,
    nome TEXT,
    periodo_gozo TEXT,
    dias REAL NOT NULL DEFAULT 0,
    incluir INTEGER NOT NULL DEFAULT 1,   -- marcado = zera o benefício
    UNIQUE(processo_id, codigo)
);
CREATE INDEX IF NOT EXISTS idx_ferias_proc ON ferias_item(processo_id);

CREATE TABLE IF NOT EXISTS resultado_beneficio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
    codigo TEXT,
    cpf TEXT,
    nome TEXT NOT NULL,
    cargo TEXT,
    departamento TEXT,
    empresa TEXT NOT NULL DEFAULT 'PISA',
    faixa_alim INTEGER,
    valor_base REAL NOT NULL DEFAULT 0,
    faltas_dias REAL NOT NULL DEFAULT 0,
    atraso_min REAL NOT NULL DEFAULT 0,
    pct_desconto REAL NOT NULL DEFAULT 0,
    valor_final REAL NOT NULL DEFAULT 0,
    pct_recebido REAL NOT NULL DEFAULT 100,
    zerado_por_atestado INTEGER NOT NULL DEFAULT 0,
    zerado_por_ferias INTEGER NOT NULL DEFAULT 0,
    motivo TEXT,
    UNIQUE(processo_id, codigo)
);
CREATE INDEX IF NOT EXISTS idx_result_proc ON resultado_beneficio(processo_id);

CREATE TABLE IF NOT EXISTS sodexo_modelo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_arquivo TEXT NOT NULL,
    conteudo_base64 TEXT NOT NULL,
    total_beneficiarios INTEGER NOT NULL DEFAULT 0,
    empresa TEXT NOT NULL DEFAULT 'PISA',
    ativo INTEGER NOT NULL DEFAULT 1,
    enviado_por_id INTEGER REFERENCES usuario(id),
    enviado_por_nome TEXT,
    enviado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
""")


def aplicar_migrations(conn) -> int:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_versao (
            versao INTEGER PRIMARY KEY,
            aplicada_em TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    cur = conn.execute("SELECT COALESCE(MAX(versao),0) FROM schema_versao;")
    versao_atual = cur.fetchone()[0]
    from src.banco.conexao import usar_postgres
    if versao_atual >= 1:
        try:
            conn.execute("SELECT 1 FROM usuario LIMIT 1;").fetchone()
        except Exception:
            versao_atual = 0
            try: conn.execute("DELETE FROM schema_versao;")
            except Exception: pass
    for i, sql in enumerate(MIGRATIONS, start=1):
        if i <= versao_atual:
            continue
        conn.executescript(sql)
        if usar_postgres():
            conn.execute("INSERT INTO schema_versao(versao) VALUES (%s) ON CONFLICT DO NOTHING;", (i,))
        else:
            conn.execute("INSERT OR IGNORE INTO schema_versao(versao) VALUES (?);", (i,))
    return len(MIGRATIONS)


# Valores das 13 faixas de alimentação (confirmados com o Erick)
FAIXAS_SEED = {
    1: 275.0, 2: 422.0, 3: 1500.0, 4: 2000.0, 5: 450.0, 6: 500.0, 7: 105.5,
    8: 800.0, 9: 137.5, 10: 1200.0, 11: 68.75, 12: 211.0, 13: 0.0,
}


def inicializar_banco() -> None:
    from src.banco.conexao import obter_conexao
    conn = obter_conexao()
    aplicar_migrations(conn)
    _garantir_estrutura(conn)
    _seed_faixas(conn)
    _criar_parametros_default(conn)


def _coluna_existe(conn, tabela: str, coluna: str) -> bool:
    """Verifica se uma coluna existe (funciona em SQLite e Postgres)."""
    from src.banco.conexao import usar_postgres
    try:
        if usar_postgres():
            row = conn.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name=? AND column_name=?;", (tabela, coluna)).fetchone()
            return row is not None
        rows = conn.execute(f"PRAGMA table_info({tabela});").fetchall()
        return any((r[1] == coluna) for r in rows)
    except Exception:
        return False


def _garantir_estrutura(conn) -> None:
    """
    Garante que estruturas adicionadas em versões novas existam mesmo em bancos
    criados antes (ex.: Neon já em uso). É idempotente e NÃO apaga dados.
    Corrige, entre outros, a coluna 'departamento' e a tabela de férias.
    """
    # Colunas novas (tabela, coluna, tipo)
    colunas = [
        ("funcionario", "departamento", "TEXT"),
        ("resultado_beneficio", "departamento", "TEXT"),
        ("resultado_beneficio", "zerado_por_ferias", "INTEGER NOT NULL DEFAULT 0"),
        ("resultado_beneficio", "zerado_por_atestado", "INTEGER NOT NULL DEFAULT 0"),
        ("funcionario", "empresa", "TEXT NOT NULL DEFAULT 'PISA'"),
        ("resultado_beneficio", "empresa", "TEXT NOT NULL DEFAULT 'PISA'"),
        ("sodexo_modelo", "empresa", "TEXT NOT NULL DEFAULT 'PISA'"),
        ("processo", "empresa", "TEXT NOT NULL DEFAULT 'PISA'"),
    ]
    for tabela, coluna, tipo in colunas:
        try:
            if not _coluna_existe(conn, tabela, coluna):
                conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo};")
        except Exception:
            pass  # se já existir ou a tabela ainda não existir, segue

    # Tabela de férias (caso o banco seja anterior à feature de Férias)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ferias_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processo_id INTEGER NOT NULL REFERENCES processo(id) ON DELETE CASCADE,
                codigo TEXT,
                nome TEXT,
                periodo_gozo TEXT,
                dias REAL NOT NULL DEFAULT 0,
                incluir INTEGER NOT NULL DEFAULT 1,
                UNIQUE(processo_id, codigo)
            );
            CREATE INDEX IF NOT EXISTS idx_ferias_proc ON ferias_item(processo_id);
        """)
    except Exception:
        pass

    # Renomeia o benefício de "Vale Refeição" para "Vale Alimentação" (bancos antigos)
    try:
        conn.execute("UPDATE parametros_sistema SET valor='Vale Alimentação' "
                     "WHERE chave='beneficio.nome' AND valor='Vale Refeição';")
    except Exception:
        pass


def _seed_faixas(conn) -> None:
    """Cria as 13 faixas se ainda não existirem (não sobrescreve valores editados)."""
    for numero, valor in FAIXAS_SEED.items():
        nome = "Sem direito" if numero == 13 else f"Faixa {numero}"
        conn.execute(
            "INSERT OR IGNORE INTO tabela_beneficio (numero, nome, valor_premio) VALUES (?, ?, ?);",
            (numero, nome, valor),
        )


def _criar_parametros_default(conn) -> None:
    defaults = {"beneficio.nome": "Vale Alimentação"}
    for chave, valor in defaults.items():
        conn.execute(
            "INSERT OR IGNORE INTO parametros_sistema (chave, valor) VALUES (?, ?);",
            (chave, valor),
        )
