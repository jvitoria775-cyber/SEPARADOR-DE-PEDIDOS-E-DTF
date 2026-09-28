"""Módulo de Produção DTF (Lista de Impressão).
Agrupa títulos iguais somando quantidades.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import operations as db


def agrupar_dtf(lista: list) -> list:
    """Agrupa itens DTF por título da estampa + produto base + cor, somando quantidades."""
    grupos = {}
    for item in lista:
        titulo_norm = (item['titulo_estampa'] or '').strip().lower()
        prod_norm = (item['produto_base'] or '').strip().lower()
        cor_norm = (item['cor'] or '').strip().lower()
        chave = (titulo_norm, prod_norm, cor_norm)

        if chave not in grupos:
            grupos[chave] = {
                'titulo_estampa': item['titulo_estampa'],
                'produto_base': item['produto_base'],
                'cor': item['cor'],
                'quantidade': 0,
                'link_imagem': item.get('link_imagem', ''),
                'ids': []  # todos os IDs individuais
            }
        grupos[chave]['quantidade'] += item['quantidade']
        grupos[chave]['ids'].append(item['id'])
    return list(grupos.values())


def render():
    """Renderiza a página de produção DTF."""
    st.header("🖨️ Produção DTF")
    st.caption("Gere a lista, marque impressos, limpe e pronto.")

    # Lotes novos sem DTF gerado
    todos_lotes = db.listar_lotes()
    lotes_sem_dtf = []
    for lote in todos_lotes:
        dtf_existente = db.listar_dtf_producao(lote['id'])
        itens_lote = db.listar_itens_lote(lote['id'])
        tem_associados = any(i['associado'] for i in itens_lote)
        if not dtf_existente and tem_associados:
            lotes_sem_dtf.append(lote)

    if lotes_sem_dtf:
        st.subheader("📦 Lotes novos para gerar DTF")
        for lote in lotes_sem_dtf:
            col1, col2 = st.columns([4, 2])
            col1.write(f"📦 {lote['nome']}")
            if col2.button("➕ Gerar DTF", key=f"gerar_dtf_{lote['id']}",
                          type="primary", use_container_width=True):
                itens = db.adicionar_dtf_de_lote(lote['id'])
                if itens:
                    st.success(f"✅ {len(itens)} estampas adicionadas!")
                    st.rerun()
                else:
                    st.warning("Nenhum item associado encontrado.")
        st.divider()

    # Lista DTF global — apenas NÃO impressos
    lista_dtf = db.listar_dtf_global()
    pendentes_raw = [i for i in lista_dtf if not i['impresso']]
    impressos_raw = [i for i in lista_dtf if i['impresso']]

    if not pendentes_raw and not impressos_raw:
        if not lotes_sem_dtf:
            st.info("📭 Nenhum DTF pendente. Importe pedidos e gere a lista.")
        return

    # Agrupar pendentes (unificar títulos iguais)
    if pendentes_raw:
        pendentes = agrupar_dtf(pendentes_raw)
        total_dtfs = sum(i['quantidade'] for i in pendentes)

        m1, m2 = st.columns(2)
        m1.metric("Estampas Pendentes", len(pendentes))
        m2.metric("Total de DTFs", total_dtfs)

        st.divider()
        st.subheader(f"📋 Lista de Impressão ({len(pendentes)} itens)")

        for idx, item in enumerate(pendentes):
            with st.container(border=True):
                col_img, col_info, col_qtd, col_btn = st.columns([1, 3, 1, 1])

                with col_img:
                    link_img = item.get('link_imagem', '')
                    if link_img and str(link_img) not in ('', 'nan', 'None') and str(link_img).startswith('http'):
                        try:
                            st.image(link_img, width=80)
                        except Exception:
                            st.write("📷")
                    else:
                        st.write("📷")

                with col_info:
                    st.markdown(f"**{item['titulo_estampa']}**")
                    st.caption(f"Produto: {item['produto_base']} | Cor: {item['cor']}")

                with col_qtd:
                    st.metric("Qtd", item['quantidade'])

                with col_btn:
                    if st.button("✅ Impresso", key=f"imp_{idx}", use_container_width=True):
                        # Marca TODOS os IDs deste grupo
                        for dtf_id in item['ids']:
                            db.atualizar_status_impressao(dtf_id, True)
                        st.rerun()

        # Marcar todos
        st.divider()
        if st.button("✅ Marcar TODOS como Impressos", use_container_width=True):
            db.marcar_todos_impressos_global(True)
            st.rerun()

        # Download
        df_dtf = pd.DataFrame([{
            'Estampa': i['titulo_estampa'],
            'Produto': i['produto_base'],
            'Cor': i['cor'],
            'Quantidade': i['quantidade'],
        } for i in pendentes])

        csv = df_dtf.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Lista DTF (.csv)",
            data=csv,
            file_name="dtf_pendentes.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Impressos — limpar
    if impressos_raw:
        st.divider()
        st.success(f"✅ {len(impressos_raw)} registros já impressos")
        if st.button(
            f"🗑️ Limpar Impressos",
            type="primary",
            use_container_width=True
        ):
            db.remover_dtf_impressos()
            st.rerun()
