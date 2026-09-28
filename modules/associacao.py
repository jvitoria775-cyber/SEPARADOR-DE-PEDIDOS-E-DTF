"""Módulo de Associação De/Para (Mapeamento de Kits e Variações).
Unifica itens com o mesmo título e permite vincular facilmente a produtos já associados.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import operations as db


def render():
    """Renderiza a página de associação De/Para."""
    st.header("🔗 Associação De/Para")
    st.caption("Associe anúncios aos produtos base. Associou = salvo permanentemente na memória.")

    produtos = db.listar_produtos_base()
    if not produtos:
        st.error("⚠️ Nenhum produto base cadastrado!")
        st.markdown("""
        ### 📌 Siga estes passos:
        
        **1️⃣ Cadastro de Produtos** ← Vá primeiro!  
        Cadastre seus produtos base com cores e tamanhos.
        
        **2️⃣ Importar Pedidos** → Upload da planilha XLSX.
        
        **3️⃣ Associação De/Para** ← Volte aqui depois.
        """)
        return

    nomes_produtos = {p['id']: p['nome'] for p in produtos}

    tab1, tab2, tab3 = st.tabs([
        "⚡ Associar Pendentes",
        "📋 Associações Salvas",
        "🏷️ Aliases (Agrupamento)"
    ])

    # ========== TAB 1: Associar Pendentes ==========
    with tab1:
        todos_lotes = db.listar_lotes()
        lotes_com_pendencias = []
        for lote in todos_lotes:
            pendentes = db.itens_nao_associados(lote['id'])
            if pendentes:
                lotes_com_pendencias.append(lote)

        if not lotes_com_pendencias:
            st.success("✅ Tudo associado! Nenhum anúncio pendente.")
            return

        col_lote, col_info = st.columns([3, 2])
        with col_lote:
            lote_selecionado = st.selectbox(
                "Lotes com pendências",
                options=lotes_com_pendencias,
                format_func=lambda x: f"📦 {x['nome']} ({x['data_importacao']})",
                key="lote_assoc"
            )

        if not lote_selecionado:
            return

        lote_id = lote_selecionado['id']
        pendentes = db.itens_nao_associados(lote_id)

        # Buscar modelos já existentes para permitir vínculo com 1 clique
        modelos_existentes = db.listar_modelos_associacao()

        with col_info:
            total_itens_pend = sum(p.get('total_pedidos', 1) for p in pendentes)
            st.info(f"⏳ **{len(pendentes)}** anúncios distintos ({total_itens_pend} pedidos)")

        for idx, item in enumerate(pendentes):
            chave = item['chave_anuncio']
            pedidos_cnt = item.get('total_pedidos', 1)
            pecas_cnt = item.get('total_pecas', 1)

            with st.container(border=True):
                col_img, col_info_card = st.columns([1, 4])

                with col_img:
                    link_img = item.get('link_imagem', '')
                    if link_img and str(link_img) not in ('', 'nan', 'None') and str(link_img).startswith('http'):
                        try:
                            st.image(link_img, width=95)
                        except Exception:
                            st.write("📷")
                    else:
                        st.write("📷 Sem foto")

                with col_info_card:
                    st.markdown(f"**📌 {item['titulo_anuncio']}**")
                    detalhes = []
                    if item.get('variacao'):
                        detalhes.append(f"Variação: **{item['variacao']}**")
                    detalhes.append(f"📦 **{pedidos_cnt} pedido(s)** ({pecas_cnt} peças)")
                    st.caption(" • ".join(detalhes))

                # Opção rápida: Vincular a um produto/anúncio já existente
                if modelos_existentes:
                    with st.expander("⚡ **Vincular ao mesmo produto de um anúncio já cadastrado**", expanded=True):
                        st.caption("Escolha um anúncio já cadastrado que use as mesmas peças/DTF:")
                        col_sel, col_btn = st.columns([3, 1])
                        with col_sel:
                            modelo_escolhido = st.selectbox(
                                "Produto já cadastrado",
                                options=modelos_existentes,
                                format_func=lambda m: f"🎯 {m['chave'][:40]}... ➔ {m['resumo']}",
                                key=f"sel_modelo_{idx}"
                            )
                        with col_btn:
                            st.write("")
                            if st.button("🔗 Vincular", key=f"btn_vincular_{idx}", type="primary", use_container_width=True):
                                if modelo_escolhido:
                                    db.clonar_associacao(
                                        chave_origem=modelo_escolhido['chave'],
                                        chave_destino=chave,
                                        link_imagem=item.get('link_imagem', '')
                                    )
                                    db.marcar_itens_associados(lote_id, chave)
                                    # Atualiza todos os lotes
                                    for l in db.listar_lotes():
                                        db.reassociar_itens_lote(l['id'])
                                    st.success("✅ Vinculado com sucesso!")
                                    st.rerun()

                # Opção manual: Montar novo produto ou kit
                with st.expander("✏️ **Ou montar nova composição (novo produto ou kit)**", expanded=(not bool(modelos_existentes))):
                    n_itens = st.number_input(
                        "Quantas peças compõem este anúncio/kit?",
                        min_value=1, max_value=20, value=1,
                        key=f"n_itens_{idx}"
                    )

                    itens_kit = []
                    for i in range(int(n_itens)):
                        st.markdown(f"**Item {i+1}:**")
                        c1, c2, c3, c4 = st.columns(4)

                        with c1:
                            prod_sel = st.selectbox(
                                "Produto Base",
                                options=list(nomes_produtos.keys()),
                                format_func=lambda x: nomes_produtos[x],
                                key=f"prod_{idx}_{i}"
                            )

                        with c2:
                            cores = db.listar_cores(prod_sel)
                            nomes_cores = [c['nome'] for c in cores] if cores else ['N/A']
                            cor_sel = st.selectbox(
                                "Cor", options=nomes_cores,
                                key=f"cor_{idx}_{i}"
                            )

                        with c3:
                            tamanhos = db.listar_tamanhos(prod_sel)
                            if not tamanhos:
                                tamanhos = ['ÚNICO']
                            tam_sel = st.selectbox(
                                "Tamanho", options=tamanhos,
                                key=f"tam_{idx}_{i}"
                            )

                        with c4:
                            qtd = st.number_input(
                                "Quantidade", min_value=1, value=1,
                                key=f"qtd_{idx}_{i}"
                            )

                        itens_kit.append({
                            'produto_base_id': prod_sel,
                            'cor': cor_sel,
                            'tamanho': tam_sel,
                            'quantidade': qtd
                        })

                    titulo_ref_custom = st.text_input(
                        "🏷️ Nome da Estampa / Título de Referência (para unificar no DTF)",
                        value=item.get('titulo_anuncio', ''),
                        key=f"ref_input_{idx}",
                        help="Títulos diferentes vinculados a esta mesma estampa serão somados juntos na lista DTF"
                    )

                    if st.button("💾 Salvar Nova Associação", key=f"btn_assoc_{idx}", type="primary", use_container_width=True):
                        db.excluir_associacoes_por_chave(chave)

                        for kit_item in itens_kit:
                            db.criar_associacao(
                                chave_anuncio=chave,
                                produto_base_id=kit_item['produto_base_id'],
                                cor=kit_item['cor'],
                                tamanho=kit_item['tamanho'],
                                quantidade=kit_item['quantidade'],
                                link_imagem=item.get('link_imagem', ''),
                                titulo_referencia=titulo_ref_custom
                            )

                        db.marcar_itens_associados(lote_id, chave)
                        for l in db.listar_lotes():
                            db.reassociar_itens_lote(l['id'])
                        st.success("✅ Associação salva!")
                        st.rerun()

    # ========== TAB 2: Associações Salvas ==========
    with tab2:
        todas = db.listar_todas_associacoes()
        if not todas:
            st.info("Nenhuma associação salva ainda.")
        else:
            agrupado = {}
            for a in todas:
                if a['chave_anuncio'] not in agrupado:
                    agrupado[a['chave_anuncio']] = []
                agrupado[a['chave_anuncio']].append(a)

            st.metric("Total de Anúncios Mapeados", len(agrupado))

            for chave, assocs in agrupado.items():
                with st.expander(f"🔗 {chave}"):
                    for a in assocs:
                        st.write(
                            f"→ **{a['produto_nome']}** | Cor: {a['cor']} | "
                            f"Tam: {a['tamanho']} | Qtd: {a['quantidade']}"
                        )
                    if st.button("🗑️ Remover Associação", key=f"del_assoc_{chave}"):
                        db.excluir_associacoes_por_chave(chave)
                        # Reavalia lotes
                        for l in db.listar_lotes():
                            db.reassociar_itens_lote(l['id'])
                        st.success("Associação removida!")
                        st.rerun()

    # ========== TAB 3: Aliases ==========
    with tab3:
        st.markdown("**Aliases** vinculam títulos variantes diretamente a uma chave principal existente.")

        with st.form("form_alias", clear_on_submit=True):
            titulo_variante = st.text_input(
                "Título Variante (título alternativo)",
                placeholder="Ex: Kit 3 Bermudas Masculinas"
            )

            todas_assocs = db.listar_todas_associacoes()
            chaves_existentes = sorted(set(a['chave_anuncio'] for a in todas_assocs))

            if chaves_existentes:
                chave_principal = st.selectbox(
                    "Chave Principal (já cadastrada)",
                    options=chaves_existentes
                )
            else:
                chave_principal = st.text_input("Chave Principal")

            if st.form_submit_button("🔗 Criar Alias", use_container_width=True):
                if titulo_variante and chave_principal:
                    variante_normalizada = db.normalizar_chave(titulo_variante)
                    db.criar_alias(variante_normalizada, chave_principal)
                    for l in db.listar_lotes():
                        db.reassociar_itens_lote(l['id'])
                    st.success("Alias criado e aplicado com sucesso!")
                    st.rerun()

        aliases = db.listar_aliases()
        if aliases:
            st.divider()
            for alias in aliases:
                c1, c2, c3 = st.columns([3, 3, 1])
                c1.write(f"📎 {alias['titulo_variante']}")
                c2.write(f"→ {alias['chave_principal']}")
                if c3.button("🗑️", key=f"del_alias_{alias['id']}"):
                    db.excluir_alias(alias['id'])
                    for l in db.listar_lotes():
                        db.reassociar_itens_lote(l['id'])
                    st.rerun()
