"""Módulo de Cadastro de Produtos Base."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import TAMANHOS_ORDEM
from database import operations as db


def render():
    """Renderiza a página de cadastro de produtos."""
    st.header("📋 Cadastro de Produtos Base")
    st.caption("Cadastre os produtos-mãe (Camiseta, Short, Baby Look, etc.) com suas cores e tamanhos disponíveis.")

    # ------ Formulário de novo produto ------
    with st.expander("➕ Novo Produto Base", expanded=False):
        with st.form("form_novo_produto", clear_on_submit=True):
            nome = st.text_input("Nome do Produto", placeholder="Ex: Camiseta, Short, Baby Look...")
            tamanhos_selecionados = st.multiselect(
                "Tamanhos Disponíveis",
                options=TAMANHOS_ORDEM,
                default=TAMANHOS_ORDEM[:4]  # P, M, G, GG
            )
            cores_input = st.text_input(
                "Cores (separadas por vírgula)",
                placeholder="Ex: Preto, Branco, Cinza, Azul Marinho"
            )
            submitted = st.form_submit_button("✅ Cadastrar Produto", use_container_width=True)

            if submitted and nome:
                try:
                    produto_id = db.criar_produto_base(nome)
                    if tamanhos_selecionados:
                        db.definir_tamanhos(produto_id, tamanhos_selecionados)
                    if cores_input:
                        for cor in cores_input.split(","):
                            cor = cor.strip()
                            if cor:
                                try:
                                    db.adicionar_cor(produto_id, cor)
                                except Exception:
                                    pass
                    st.success(f"✅ Produto '{nome}' cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {e}")

    # ------ Lista de produtos cadastrados ------
    st.divider()
    produtos = db.listar_produtos_base()

    if not produtos:
        st.info("Nenhum produto cadastrado ainda. Use o formulário acima para começar.")
        return

    for produto in produtos:
        with st.expander(f"🏷️ {produto['nome']}", expanded=False):
            col1, col2 = st.columns(2)

            # Tamanhos
            with col1:
                st.markdown("**Tamanhos:**")
                tamanhos = db.listar_tamanhos(produto['id'])
                if tamanhos:
                    st.write(" → ".join(tamanhos))
                else:
                    st.caption("Nenhum tamanho definido")

                # Editar tamanhos
                novos_tamanhos = st.multiselect(
                    "Editar tamanhos",
                    options=TAMANHOS_ORDEM,
                    default=tamanhos,
                    key=f"tam_{produto['id']}"
                )
                if st.button("💾 Salvar Tamanhos", key=f"btn_tam_{produto['id']}"):
                    db.definir_tamanhos(produto['id'], novos_tamanhos)
                    st.success("Tamanhos atualizados!")
                    st.rerun()

            # Cores
            with col2:
                st.markdown("**Cores:**")
                cores = db.listar_cores(produto['id'])
                if cores:
                    for cor in cores:
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"🎨 {cor['nome']}")
                        if c2.button("🗑️", key=f"del_cor_{cor['id']}"):
                            db.excluir_cor(cor['id'])
                            st.rerun()
                else:
                    st.caption("Nenhuma cor cadastrada")

                # Adicionar cor
                nova_cor = st.text_input("Nova cor", key=f"nova_cor_{produto['id']}")
                if st.button("➕ Adicionar Cor", key=f"btn_cor_{produto['id']}"):
                    if nova_cor:
                        try:
                            db.adicionar_cor(produto['id'], nova_cor)
                            st.success(f"Cor '{nova_cor}' adicionada!")
                            st.rerun()
                        except Exception:
                            st.warning("Cor já existe.")

            # Botão excluir produto
            st.divider()
            if st.button(f"🗑️ Excluir Produto '{produto['nome']}'", key=f"del_prod_{produto['id']}",
                         type="secondary"):
                db.excluir_produto_base(produto['id'])
                st.success(f"Produto '{produto['nome']}' excluído.")
                st.rerun()
