"""Modelos e inicialização do banco de dados (Supabase PostgreSQL / SQLite local)."""
import os
import sqlite3

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "pedidos.db"
)

TAMANHOS_ORDEM = [
    # Infantil / Bebê
    "RN", "BB", "0", "1", "2", "3", "4", "6", "8", "10", "12", "14", "16",
    # Adulto
    "PP", "P", "M", "G", "GG", "XG", "XXG",
    # Plus Size
    "G1", "G2", "G3", "G4", "G5", "G6", "G7",
    # Outros
    "ÚNICO"
]


class PostgresCursorWrapper:
    def __init__(self, cursor):
        self._cur = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        pg_query = query.replace('?', '%s')
        is_insert = pg_query.strip().upper().startswith('INSERT')

        if is_insert and 'RETURNING' not in pg_query.upper():
            pg_query_ret = pg_query.rstrip().rstrip(';') + ' RETURNING id;'
            try:
                self._cur.execute("SAVEPOINT insert_savepoint;")
                if params is not None:
                    self._cur.execute(pg_query_ret, params)
                else:
                    self._cur.execute(pg_query_ret)
                row = self._cur.fetchone()
                if row and 'id' in row:
                    self.lastrowid = row['id']
                self._cur.execute("RELEASE SAVEPOINT insert_savepoint;")
                return self
            except Exception:
                self._cur.execute("ROLLBACK TO SAVEPOINT insert_savepoint;")

        if params is not None:
            self._cur.execute(pg_query, params)
        else:
            self._cur.execute(pg_query)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def executescript(self, script):
        self._cur.execute(script)
        return self

    def __iter__(self):
        return iter(self._cur)


class PostgresConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def execute(self, query, params=None):
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def get_connection():
    """Retorna conexão com o banco de dados (Supabase PostgreSQL ou SQLite local como fallback)."""
    if HAS_PSYCOPG2:
        try:
            db_url = None
            try:
                import streamlit as st
                db_url = st.secrets.get("DATABASE_URL")
            except Exception:
                pass

            if not db_url:
                db_url = os.environ.get("DATABASE_URL")

            if db_url:
                raw_conn = psycopg2.connect(db_url, sslmode='require', connect_timeout=5)
            else:
                raw_conn = psycopg2.connect(
                    host=os.environ.get("SUPABASE_HOST", "db.pjnzxizkbtclarvfryue.supabase.co"),
                    port=int(os.environ.get("SUPABASE_PORT", 5432)),
                    user=os.environ.get("SUPABASE_USER", "postgres"),
                    password=os.environ.get("SUPABASE_PASSWORD", "#Familia0522"),
                    dbname=os.environ.get("SUPABASE_DB", "postgres"),
                    sslmode='require',
                    connect_timeout=5
                )
            return PostgresConnectionWrapper(raw_conn)
        except Exception:
            pass  # Fallback para SQLite se falhar a conexão remota

    # Conexão SQLite local de contingência
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn



POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos_base (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cores (
    id SERIAL PRIMARY KEY,
    produto_base_id INTEGER NOT NULL REFERENCES produtos_base(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    UNIQUE(produto_base_id, nome)
);

CREATE TABLE IF NOT EXISTS tamanhos_produto (
    id SERIAL PRIMARY KEY,
    produto_base_id INTEGER NOT NULL REFERENCES produtos_base(id) ON DELETE CASCADE,
    tamanho TEXT NOT NULL,
    ordem INTEGER NOT NULL,
    UNIQUE(produto_base_id, tamanho)
);

CREATE TABLE IF NOT EXISTS lotes_importacao (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    arquivo_original TEXT,
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    concluido INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_importacao(id) ON DELETE CASCADE,
    numero_pedido TEXT NOT NULL,
    titulo_anuncio TEXT,
    sku TEXT,
    variacao TEXT,
    quantidade INTEGER NOT NULL DEFAULT 1,
    link_imagem TEXT,
    chave_anuncio TEXT,
    associado INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS associacoes (
    id SERIAL PRIMARY KEY,
    chave_anuncio TEXT NOT NULL,
    produto_base_id INTEGER NOT NULL REFERENCES produtos_base(id),
    cor TEXT NOT NULL,
    tamanho TEXT NOT NULL,
    quantidade INTEGER NOT NULL DEFAULT 1,
    link_imagem TEXT,
    titulo_referencia TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aliases (
    id SERIAL PRIMARY KEY,
    titulo_variante TEXT NOT NULL UNIQUE,
    chave_principal TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dtf_producao (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes_importacao(id),
    titulo_estampa TEXT NOT NULL,
    produto_base TEXT NOT NULL,
    cor TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    link_imagem TEXT,
    impresso INTEGER DEFAULT 0,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_associacoes_chave ON associacoes(chave_anuncio);
CREATE INDEX IF NOT EXISTS idx_aliases_variante ON aliases(titulo_variante);
CREATE INDEX IF NOT EXISTS idx_itens_lote ON itens_pedido(lote_id);
CREATE INDEX IF NOT EXISTS idx_dtf_lote ON dtf_producao(lote_id);
"""


def init_db():
    """Cria todas as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()

    if isinstance(conn, PostgresConnectionWrapper):
        cursor.execute(POSTGRES_SCHEMA)
        conn.commit()
        conn.close()
        return

    cursor.executescript("""
        -- Produtos base (ex: Camiseta, Short, Baby Look)
        CREATE TABLE IF NOT EXISTS produtos_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Cores disponíveis por produto
        CREATE TABLE IF NOT EXISTS cores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_base_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            FOREIGN KEY (produto_base_id) REFERENCES produtos_base(id) ON DELETE CASCADE,
            UNIQUE(produto_base_id, nome)
        );

        -- Tamanhos habilitados por produto
        CREATE TABLE IF NOT EXISTS tamanhos_produto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_base_id INTEGER NOT NULL,
            tamanho TEXT NOT NULL,
            ordem INTEGER NOT NULL,
            FOREIGN KEY (produto_base_id) REFERENCES produtos_base(id) ON DELETE CASCADE,
            UNIQUE(produto_base_id, tamanho)
        );

        -- Lotes de importação
        CREATE TABLE IF NOT EXISTS lotes_importacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            arquivo_original TEXT,
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Itens de cada pedido importado
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER NOT NULL,
            numero_pedido TEXT NOT NULL,
            titulo_anuncio TEXT,
            sku TEXT,
            variacao TEXT,
            quantidade INTEGER NOT NULL DEFAULT 1,
            link_imagem TEXT,
            chave_anuncio TEXT,
            associado INTEGER DEFAULT 0,
            FOREIGN KEY (lote_id) REFERENCES lotes_importacao(id) ON DELETE CASCADE
        );

        -- Associações De/Para: chave_anuncio -> produto base + cor + tamanho
        CREATE TABLE IF NOT EXISTS associacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave_anuncio TEXT NOT NULL,
            produto_base_id INTEGER NOT NULL,
            cor TEXT NOT NULL,
            tamanho TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1,
            link_imagem TEXT,
            titulo_referencia TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_base_id) REFERENCES produtos_base(id)
        );

        -- Aliases: títulos diferentes que mapeiam para a mesma chave
        CREATE TABLE IF NOT EXISTS aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo_variante TEXT NOT NULL UNIQUE,
            chave_principal TEXT NOT NULL
        );

        -- Produção DTF com controle de impressão
        CREATE TABLE IF NOT EXISTS dtf_producao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER NOT NULL,
            titulo_estampa TEXT NOT NULL,
            produto_base TEXT NOT NULL,
            cor TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            link_imagem TEXT,
            impresso INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lote_id) REFERENCES lotes_importacao(id)
        );

        -- Índices para performance
        CREATE INDEX IF NOT EXISTS idx_associacoes_chave ON associacoes(chave_anuncio);
        CREATE INDEX IF NOT EXISTS idx_aliases_variante ON aliases(titulo_variante);
        CREATE INDEX IF NOT EXISTS idx_itens_lote ON itens_pedido(lote_id);
        CREATE INDEX IF NOT EXISTS idx_dtf_lote ON dtf_producao(lote_id);
    """)

    # Migração: adicionar coluna 'concluido' em lotes_importacao (separação descartável)
    try:
        cursor.execute("ALTER TABLE lotes_importacao ADD COLUMN concluido INTEGER DEFAULT 0")
    except Exception:
        pass  # Coluna já existe

    # Migração: adicionar coluna 'titulo_referencia' em associacoes (unificação de títulos)
    try:
        cursor.execute("ALTER TABLE associacoes ADD COLUMN titulo_referencia TEXT")
    except Exception:
        pass

    conn.commit()
    conn.close()
