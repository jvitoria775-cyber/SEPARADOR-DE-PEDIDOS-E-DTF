"""Módulo de Cadastro de Produtos Base.
Suporte completo a tamanhos infantis, adultos, plus size e personalizados.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import TAMANHOS_ORDEM
from database import operations as db

GRADE_INFANTIL = ["1", "2", "3", "4", "6", "8", "10", "12", "14", "16"]
GRADE_ADULTO = ["P", "M", "G", "GG", "G1", "G2", "G3"]


def render():
    """Renderiza a página de cadastro de produtos."""
    st.header("📋 Cadastro de Produtos Base")
    st.caption("Cadastre os produtos-mãe (Camiseta, Short, Conjunto Infantil, etc.) com suas cores e grade de tamanhos.")

    # ------ Formulário de novo produto ------
    with st.expander("➕ Novo Produto Base", expanded=False):
        with st.form("form_novo_produto", clear_on_submit=True):
            nome = st.text_input("Nome do Produto", placeholder="Ex: Camiseta, Camiseta Infantil, Short Tactel...")

            # Opções de grade padrão
            tipo_grade = st.radio(
                "Sugestão de Grade Rápida:",
                ["👕 Adulto Padrão (P, M, G, GG)", "👶 Infantil Padrão (2 a 16)", "✨ Personalizado"],
                horizontal=True
            )

            if tipo_grade == "👶 Infantil Padrão (2 a 16)":
                default_tams = [t for t in GRADE_INFANTIL if t in TAMANHOS_ORDEM]
            elif tipo_grade == "👕 Adulto Padrão (P, M, G, GG)":
                default_tams = ["P", "M", "G", "GG"]
            else:
                default_tams = ["P", "M", "G", "GG"]

            tamanhos_selecionados = st.multiselect(
                "Tamanhos da Lista",
                options=TAMANHOS_ORDEM,
                default=default_tams,
                help="Selecione os tamanhos infantis ou adultos disponíveis"
            )

            tamanhos_extras = st.text_input(
                "➕ Tamanhos Extras / Personalizados (separados por vírgula)",
                placeholder="Ex: 1 ano, 2 anos, Especial, RN, 0"
            )

            cores_input = st.text_input(
                "Cores (separadas por vírgula)",
                placeholder="Ex: Preto, Branco, Cinza, Azul Marinho, Vermelho"
            )

            submitted = st.form_submit_button("✅ Cadastrar Produto", use_container_width=True)

            if submitted and nome:
                try:
                    produto_id = db.criar_produto_base(nome)

                    # Une tamanhos selecionados com os extras digitados
                    lista_final_tams = list(tamanhos_selecionados)
                    if tamanhos_extras:
                        for t_extra in tamanhos_extras.split(","):
                            t_clean = t_extra.strip().upper()
                            if t_clean and t_clean not in lista_final_tams:
                                lista_final_tams.append(t_clean)

                    if lista_final_tams:
                        db.definir_tamanhos(produto_id, lista_final_tams)

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
                st.markdown("**Grade de Tamanhos:**")
                tamanhos = db.listar_tamanhos(produto['id'])
                if tamanhos:
                    st.write(" → ".join([f"`{t}`" for t in tamanhos]))
                else:
                    st.caption("Nenhum tamanho definido")

                # Todas as opções disponíveis para o multiselect (TAMANHOS_ORDEM + tamanhos já salvos)
                todas_opcoes_tam = list(dict.fromkeys(TAMANHOS_ORDEM + tamanhos))

                novos_tamanhos = st.multiselect(
                    "Editar tamanhos da grade:",
                    options=todas_opcoes_tam,
                    default=tamanhos,
                    key=f"tam_{produto['id']}"
                )

                col_add_tam, col_btn_add = st.columns([3, 1])
                with col_add_tam:
                    novo_tam_custom = st.text_input(
                        "Adicionar tamanho infantil/personalizado",
                        placeholder="Ex: 2, 4, 6, 8, 10, 12, 14...",
                        key=f"input_tam_{produto['id']}"
                    )
                with col_btn_add:
                    st.write("")
                    if st.button("➕ Adicionar", key=f"btn_add_tam_{produto['id']}", use_container_width=True):
                        if novo_tam_custom:
                            for t in novo_tam_custom.split(","):
                                db.adicionar_tamanho(produto['id'], t.strip())
                            st.success("Tamanho adicionado!")
                            st.rerun()

                if st.button("💾 Salvar Grade de Tamanhos", key=f"btn_tam_{produto['id']}", use_container_width=True):
                    db.definir_tamanhos(produto['id'], novos_tamanhos)
                    st.success("Tamanhos atualizados!")
                    st.rerun()

            # Cores
            with col2:
                st.markdown("**Cores Disponíveis:**")
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
                nova_cor = st.text_input("Nova cor", key=f"nova_cor_{produto['id']}", placeholder="Ex: Vermelho, Preto...")
                if st.button("➕ Adicionar Cor", key=f"btn_cor_{produto['id']}", use_container_width=True):
                    if nova_cor:
                        try:
                            for c in nova_cor.split(","):
                                c = c.strip()
                                if c:
                                    db.adicionar_cor(produto['id'], c)
                            st.success("Cor(es) adicionada(s)!")
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
