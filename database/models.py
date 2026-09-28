"""Modelos e inicialização do banco de dados SQLite."""
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "pedidos.db"
)

TAMANHOS_ORDEM = ["P", "M", "G", "GG", "G1", "G2", "G3", "G4", "G5"]


def get_connection():
    """Retorna conexão SQLite com row_factory habilitado."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Cria todas as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()

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
