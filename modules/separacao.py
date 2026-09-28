"""Módulo de Lista de Separação (Packing List).
Gera lista simples no formato bloco de notas.
Concluiu o lote = some da tela.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import operations as db


def gerar_texto_separacao(lista: list) -> str:
    """Gera texto formatado da lista de separação."""
    if not lista:
        return ""

    texto = ""
    produto_atual = ""
    total_geral = 0

    for item in lista:
        if item['produto'] != produto_atual:
            if produto_atual:
                texto += "\n"
            produto_atual = item['produto']
            texto += f"{produto_atual.upper()}\n\n"

        texto += f"{item['cor'].upper()} {item['tamanho']} {item['quantidade']}\n"
        total_geral += item['quantidade']

    texto += f"\n{'='*30}\nTOTAL: {total_geral} PEÇAS\n"
    return texto


def render():
    """Renderiza a página de lista de separação."""
    st.header("📝 Lista de Separação")
    st.caption("Gere a lista, separe os produtos, conclua e pronto.")

    lotes_ativos = db.listar_lotes_ativos()

    if not lotes_ativos:
        st.info("📭 Nenhum lote pendente. Importe uma nova planilha para gerar uma lista.")
        return

    lote_selecionado = st.selectbox(
        "Selecione o Lote",
        options=lotes_ativos,
        format_func=lambda x: f"📦 {x['nome']} ({x['data_importacao']})",
        key="lote_sep"
    )

    if not lote_selecionado:
        return

    lote_id = lote_selecionado['id']

    pendentes = db.itens_nao_associados(lote_id)
    if pendentes:
        st.warning(
            f"⚠️ {len(pendentes)} anúncios pendentes de associação. "
            f"Resolva em 'Associação De/Para' antes."
        )

    col1, col2 = st.columns(2)

    with col1:
        gerar = st.button("📋 Gerar Lista de Separação", type="primary", use_container_width=True)

    with col2:
        if st.button("✅ Concluir e Descartar", use_container_width=True):
            db.concluir_lote(lote_id)
            st.rerun()

    if gerar:
        lista = db.gerar_lista_separacao(lote_id)

        if not lista:
            st.warning("Nenhum item associado encontrado neste lote.")
            return

        texto = gerar_texto_separacao(lista)

        total_pecas = sum(i['quantidade'] for i in lista)
        st.metric("Total de Peças", total_pecas)
        st.divider()
        st.code(texto, language=None)

        st.download_button(
            label="📥 Baixar Lista (.txt)",
            data=texto.encode('utf-8'),
            file_name=f"separacao_{lote_selecionado['nome'].replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )
