"""Operações CRUD para o banco de dados."""
import re
from .models import get_connection, TAMANHOS_ORDEM


# ============================================================
# UTILIDADES
# ============================================================

def normalizar_chave(titulo: str, variacao: str = "") -> str:
    """Gera chave normalizada a partir do título + variação."""
    texto = f"{titulo or ''}|{variacao or ''}".strip()
    texto = re.sub(r'\s+', ' ', texto).lower().strip()
    return texto


def ordem_tamanho(tamanho: str) -> int:
    """Retorna a ordem numérica de um tamanho para ordenação."""
    try:
        return TAMANHOS_ORDEM.index(tamanho.upper().strip())
    except ValueError:
        return 999


# ============================================================
# PRODUTOS BASE
# ============================================================

def criar_produto_base(nome: str) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO produtos_base (nome) VALUES (?)", (nome.strip(),)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_produtos_base() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM produtos_base ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def excluir_produto_base(produto_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM produtos_base WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()


# ============================================================
# CORES
# ============================================================

def adicionar_cor(produto_base_id: int, nome_cor: str) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO cores (produto_base_id, nome) VALUES (?, ?)",
            (produto_base_id, nome_cor.strip())
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_cores(produto_base_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM cores WHERE produto_base_id = ? ORDER BY nome",
        (produto_base_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def excluir_cor(cor_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM cores WHERE id = ?", (cor_id,))
    conn.commit()
    conn.close()


# ============================================================
# TAMANHOS
# ============================================================

def definir_tamanhos(produto_base_id: int, tamanhos: list):
    """Define os tamanhos disponíveis para um produto base."""
    conn = get_connection()
    conn.execute("DELETE FROM tamanhos_produto WHERE produto_base_id = ?", (produto_base_id,))
    for tam in tamanhos:
        ordem = ordem_tamanho(tam)
        conn.execute(
            "INSERT INTO tamanhos_produto (produto_base_id, tamanho, ordem) VALUES (?, ?, ?)",
            (produto_base_id, tam.upper().strip(), ordem)
        )
    conn.commit()
    conn.close()


def listar_tamanhos(produto_base_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT tamanho FROM tamanhos_produto WHERE produto_base_id = ? ORDER BY ordem",
        (produto_base_id,)
    ).fetchall()
    conn.close()
    return [r['tamanho'] for r in rows]


# ============================================================
# ASSOCIAÇÕES (DE/PARA)
# ============================================================

def criar_associacao(chave_anuncio: str, produto_base_id: int, cor: str,
                     tamanho: str, quantidade: int = 1, link_imagem: str = None,
                     titulo_referencia: str = None) -> int:
    conn = get_connection()
    try:
        ref = (titulo_referencia or chave_anuncio).strip()
        cursor = conn.execute(
            """INSERT INTO associacoes 
               (chave_anuncio, produto_base_id, cor, tamanho, quantidade, link_imagem, titulo_referencia)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chave_anuncio, produto_base_id, cor.strip(), tamanho.strip().upper(),
             quantidade, link_imagem, ref)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def buscar_associacoes(chave_anuncio: str) -> list:
    """Busca associações diretas ou via alias."""
    conn = get_connection()
    # Primeiro tenta direto
    rows = conn.execute(
        """SELECT a.*, pb.nome as produto_nome 
           FROM associacoes a 
           JOIN produtos_base pb ON a.produto_base_id = pb.id
           WHERE a.chave_anuncio = ?""",
        (chave_anuncio,)
    ).fetchall()

    # Se não encontrou, tenta via alias
    if not rows:
        alias = conn.execute(
            "SELECT chave_principal FROM aliases WHERE titulo_variante = ?",
            (chave_anuncio,)
        ).fetchone()
        if alias:
            rows = conn.execute(
                """SELECT a.*, pb.nome as produto_nome 
                   FROM associacoes a 
                   JOIN produtos_base pb ON a.produto_base_id = pb.id
                   WHERE a.chave_anuncio = ?""",
                (alias['chave_principal'],)
            ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def listar_todas_associacoes() -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT a.*, pb.nome as produto_nome 
           FROM associacoes a 
           JOIN produtos_base pb ON a.produto_base_id = pb.id
           ORDER BY a.chave_anuncio, pb.nome"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def excluir_associacoes_por_chave(chave_anuncio: str):
    conn = get_connection()
    conn.execute("DELETE FROM associacoes WHERE chave_anuncio = ?", (chave_anuncio,))
    conn.commit()
    conn.close()


def listar_modelos_associacao() -> list:
    """Retorna lista de todas as associações já cadastradas com resumo amigável."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT a.*, pb.nome as produto_nome 
           FROM associacoes a 
           JOIN produtos_base pb ON a.produto_base_id = pb.id
           ORDER BY a.chave_anuncio, a.id"""
    ).fetchall()
    conn.close()

    modelos = {}
    for r in rows:
        chave = r['chave_anuncio']
        if chave not in modelos:
            modelos[chave] = {
                'chave': chave,
                'titulo_referencia': r.get('titulo_referencia') or chave,
                'link_imagem': r['link_imagem'] or '',
                'itens': []
            }
        modelos[chave]['itens'].append({
            'produto_base_id': r['produto_base_id'],
            'produto_nome': r['produto_nome'],
            'cor': r['cor'],
            'tamanho': r['tamanho'],
            'quantidade': r['quantidade']
        })

    resultado = []
    for chave, dados in modelos.items():
        descricoes = [
            f"{i['produto_nome']} {i['cor']} {i['tamanho']} (x{i['quantidade']})"
            for i in dados['itens']
        ]
        dados['resumo'] = " + ".join(descricoes)
        resultado.append(dados)
    return resultado


def clonar_associacao(chave_origem: str, chave_destino: str, link_imagem: str = None):
    """Copia a regra de chave_origem para chave_destino e padroniza titulo_referencia."""
    criar_alias(chave_destino, chave_origem)

    conn = get_connection()
    conn.execute("DELETE FROM associacoes WHERE chave_anuncio = ?", (chave_destino,))
    origens = conn.execute(
        "SELECT * FROM associacoes WHERE chave_anuncio = ?", (chave_origem,)
    ).fetchall()

    for o in origens:
        img = o['link_imagem'] or link_imagem
        titulo_ref = o.get('titulo_referencia') or chave_origem
        conn.execute(
            """INSERT INTO associacoes 
               (chave_anuncio, produto_base_id, cor, tamanho, quantidade, link_imagem, titulo_referencia)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chave_destino, o['produto_base_id'], o['cor'], o['tamanho'], o['quantidade'], img, titulo_ref)
        )
    conn.commit()
    conn.close()


# ============================================================
# ALIASES
# ============================================================

def criar_alias(titulo_variante: str, chave_principal: str) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT OR REPLACE INTO aliases (titulo_variante, chave_principal) VALUES (?, ?)",
            (titulo_variante, chave_principal)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_aliases() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM aliases ORDER BY chave_principal").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def excluir_alias(alias_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM aliases WHERE id = ?", (alias_id,))
    conn.commit()
    conn.close()


# ============================================================
# LOTES E ITENS DE PEDIDO
# ============================================================

def criar_lote(nome: str, arquivo_original: str = None) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO lotes_importacao (nome, arquivo_original) VALUES (?, ?)",
        (nome, arquivo_original)
    )
    conn.commit()
    lote_id = cursor.lastrowid
    conn.close()
    return lote_id


def listar_lotes() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM lotes_importacao ORDER BY data_importacao DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_lotes_ativos() -> list:
    """Lista apenas lotes NÃO concluídos (para separação)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM lotes_importacao WHERE concluido = 0 ORDER BY data_importacao DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def concluir_lote(lote_id: int):
    """Marca lote como concluído (separação feita, descarta lista)."""
    conn = get_connection()
    conn.execute(
        "UPDATE lotes_importacao SET concluido = 1 WHERE id = ?",
        (lote_id,)
    )
    conn.commit()
    conn.close()


def reabrir_lote(lote_id: int):
    """Reabre um lote concluído."""
    conn = get_connection()
    conn.execute(
        "UPDATE lotes_importacao SET concluido = 0 WHERE id = ?",
        (lote_id,)
    )
    conn.commit()
    conn.close()


def inserir_item_pedido(lote_id: int, numero_pedido: str, titulo_anuncio: str,
                        sku: str, variacao: str, quantidade: int,
                        link_imagem: str) -> int:
    chave = normalizar_chave(titulo_anuncio, variacao)
    # Verifica se já existe associação
    assocs = buscar_associacoes(chave)
    associado = 1 if assocs else 0

    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO itens_pedido 
           (lote_id, numero_pedido, titulo_anuncio, sku, variacao, 
            quantidade, link_imagem, chave_anuncio, associado)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (lote_id, numero_pedido, titulo_anuncio, sku, variacao,
         quantidade, link_imagem, chave, associado)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def listar_itens_lote(lote_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM itens_pedido WHERE lote_id = ? ORDER BY numero_pedido",
        (lote_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def itens_nao_associados(lote_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT chave_anuncio, titulo_anuncio, variacao, link_imagem,
                  COUNT(*) as total_pedidos, SUM(quantidade) as total_pecas
           FROM itens_pedido 
           WHERE lote_id = ? AND associado = 0
           GROUP BY chave_anuncio
           ORDER BY titulo_anuncio""",
        (lote_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def todos_itens_nao_associados() -> list:
    """Retorna itens não associados de todos os lotes ativos, agrupados por chave."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT ip.chave_anuncio, ip.titulo_anuncio, ip.variacao, ip.link_imagem,
                  COUNT(*) as total_pedidos, SUM(ip.quantidade) as total_pecas
           FROM itens_pedido ip
           JOIN lotes_importacao l ON ip.lote_id = l.id
           WHERE ip.associado = 0 AND l.concluido = 0
           GROUP BY ip.chave_anuncio
           ORDER BY ip.titulo_anuncio"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def marcar_itens_associados(lote_id: int, chave_anuncio: str):
    conn = get_connection()
    conn.execute(
        "UPDATE itens_pedido SET associado = 1 WHERE lote_id = ? AND chave_anuncio = ?",
        (lote_id, chave_anuncio)
    )
    conn.commit()
    conn.close()


def reassociar_itens_lote(lote_id: int):
    """Reavalia associações de todos os itens de um lote."""
    itens = listar_itens_lote(lote_id)
    conn = get_connection()
    for item in itens:
        assocs = buscar_associacoes(item['chave_anuncio'])
        novo_status = 1 if assocs else 0
        conn.execute(
            "UPDATE itens_pedido SET associado = ? WHERE id = ?",
            (novo_status, item['id'])
        )
    conn.commit()
    conn.close()


# ============================================================
# PRODUÇÃO DTF
# ============================================================

def gerar_lista_dtf(lote_id: int) -> list:
    """Gera lista de produção DTF com base nos itens associados do lote,
    unificando anúncios com títulos diferentes que apontam para a mesma estampa de referência.
    """
    itens = listar_itens_lote(lote_id)
    producao = {}  # chave: (titulo_estampa_lower, produto_base_lower, cor_lower)

    for item in itens:
        if not item['associado']:
            continue
        assocs = buscar_associacoes(item['chave_anuncio'])
        for assoc in assocs:
            # Título unificado da estampa
            titulo_unificado = (
                assoc.get('titulo_referencia')
                or assoc.get('chave_anuncio')
                or item.get('titulo_anuncio')
                or ''
            ).strip()

            # Imagem de referência da estampa
            img_unificada = assoc.get('link_imagem') or item.get('link_imagem', '')

            chave_dtf = (
                titulo_unificado.lower(),
                assoc['produto_nome'].strip().lower(),
                assoc['cor'].strip().lower()
            )

            if chave_dtf not in producao:
                producao[chave_dtf] = {
                    'titulo_estampa': titulo_unificado,
                    'produto_base': assoc['produto_nome'],
                    'cor': assoc['cor'],
                    'quantidade': 0,
                    'link_imagem': img_unificada,
                }
            producao[chave_dtf]['quantidade'] += assoc['quantidade'] * item['quantidade']

    return list(producao.values())


def salvar_lista_dtf(lote_id: int, itens_dtf: list):
    """Salva lista DTF no banco para controle de impressão."""
    conn = get_connection()
    # Limpa lista anterior do lote
    conn.execute("DELETE FROM dtf_producao WHERE lote_id = ?", (lote_id,))
    for item in itens_dtf:
        conn.execute(
            """INSERT INTO dtf_producao 
               (lote_id, titulo_estampa, produto_base, cor, quantidade, link_imagem)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (lote_id, item['titulo_estampa'], item['produto_base'],
             item['cor'], item['quantidade'], item.get('link_imagem', ''))
        )
    conn.commit()
    conn.close()


def listar_dtf_producao(lote_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM dtf_producao WHERE lote_id = ? ORDER BY produto_base, cor",
        (lote_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def atualizar_status_impressao(dtf_id: int, impresso: bool):
    conn = get_connection()
    conn.execute(
        "UPDATE dtf_producao SET impresso = ? WHERE id = ?",
        (1 if impresso else 0, dtf_id)
    )
    conn.commit()
    conn.close()


def marcar_todos_impressos(lote_id: int, impresso: bool):
    conn = get_connection()
    conn.execute(
        "UPDATE dtf_producao SET impresso = ? WHERE lote_id = ?",
        (1 if impresso else 0, lote_id)
    )
    conn.commit()
    conn.close()


def marcar_todos_impressos_global(impresso: bool):
    """Marca todos os DTFs de todos os lotes."""
    conn = get_connection()
    conn.execute(
        "UPDATE dtf_producao SET impresso = ?",
        (1 if impresso else 0,)
    )
    conn.commit()
    conn.close()


def listar_dtf_global(apenas_pendentes: bool = False) -> list:
    """Lista TODOS os DTFs de todos os lotes (visão acumulada).
    
    Agrupa por titulo_estampa + produto_base + cor, somando quantidades
    de lotes diferentes.
    """
    conn = get_connection()
    if apenas_pendentes:
        rows = conn.execute(
            """SELECT * FROM dtf_producao 
               WHERE impresso = 0 
               ORDER BY produto_base, cor, titulo_estampa"""
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM dtf_producao 
               ORDER BY impresso ASC, produto_base, cor, titulo_estampa"""
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remover_dtf_impressos():
    """Remove permanentemente todos os DTFs marcados como impressos."""
    conn = get_connection()
    conn.execute("DELETE FROM dtf_producao WHERE impresso = 1")
    conn.commit()
    conn.close()


def contar_dtf_status() -> dict:
    """Retorna contadores globais do DTF."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as n FROM dtf_producao").fetchone()['n']
    impressos = conn.execute("SELECT COUNT(*) as n FROM dtf_producao WHERE impresso = 1").fetchone()['n']
    pendentes = total - impressos
    qtd_total = conn.execute("SELECT COALESCE(SUM(quantidade), 0) as n FROM dtf_producao").fetchone()['n']
    qtd_pendente = conn.execute("SELECT COALESCE(SUM(quantidade), 0) as n FROM dtf_producao WHERE impresso = 0").fetchone()['n']
    conn.close()
    return {
        'total': total,
        'impressos': impressos,
        'pendentes': pendentes,
        'qtd_total': qtd_total,
        'qtd_pendente': qtd_pendente
    }


def adicionar_dtf_de_lote(lote_id: int):
    """Gera DTF do lote e ADICIONA à lista global (não substitui).
    
    Se o lote já teve DTF gerado, recria apenas os itens daquele lote.
    """
    # Limpa itens antigos APENAS deste lote
    conn = get_connection()
    conn.execute("DELETE FROM dtf_producao WHERE lote_id = ?", (lote_id,))
    conn.commit()
    conn.close()
    
    # Gera e salva novos itens para este lote
    itens_dtf = gerar_lista_dtf(lote_id)
    if itens_dtf:
        salvar_lista_dtf(lote_id, itens_dtf)
    return itens_dtf


# ============================================================
# LISTA DE SEPARAÇÃO (PACKING LIST)
# ============================================================

def gerar_lista_separacao(lote_id: int) -> list:
    """Gera packing list agrupada por produto, cor, tamanho (ordem progressiva)."""
    itens = listar_itens_lote(lote_id)
    separacao = {}  # (produto, cor, tamanho) -> {dados + quantidade}

    for item in itens:
        if not item['associado']:
            continue
        assocs = buscar_associacoes(item['chave_anuncio'])
        for assoc in assocs:
            chave = (assoc['produto_nome'], assoc['cor'], assoc['tamanho'])
            if chave not in separacao:
                separacao[chave] = {
                    'produto': assoc['produto_nome'],
                    'cor': assoc['cor'],
                    'tamanho': assoc['tamanho'],
                    'quantidade': 0,
                    'pedidos': []
                }
            qtd = assoc['quantidade'] * item['quantidade']
            separacao[chave]['quantidade'] += qtd
            separacao[chave]['pedidos'].append(item['numero_pedido'])

    # Ordena: produto -> cor -> tamanho (ordem progressiva)
    resultado = sorted(
        separacao.values(),
        key=lambda x: (x['produto'], x['cor'], ordem_tamanho(x['tamanho']))
    )
    return resultado
