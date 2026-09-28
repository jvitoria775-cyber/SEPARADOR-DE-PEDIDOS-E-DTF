"""Módulo de Importação de Pedidos (Planilha UpSeller)."""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import operations as db

# Possíveis nomes de colunas no UpSeller (mapeamento flexível)
COLUMN_MAP = {
    'numero_pedido': [
        'Nº de Pedido', 'Nº do Pedido', 'Numero do Pedido', 'Numero de Pedido',
        'N° de Pedido', 'Order Number', 'Pedido', 'nº de pedido',
        'Número do Pedido', 'Número de Pedido', 'N Pedido'
    ],
    'titulo_anuncio': [
        'Nome do Anúncio', 'Título do Anúncio', 'Nome do Produto',
        'Titulo do Anuncio', 'Nome do Anuncio', 'Product Name',
        'Título', 'Anúncio', 'titulo do anuncio', 'nome do anúncio',
        'Produto'
    ],
    'sku': [
        'SKU', 'Sku', 'sku', 'SKU do Produto', 'SKU Produto',
        'Código SKU', 'Codigo SKU'
    ],
    'variacao': [
        'Variação', 'Variacao', 'Cor/Tamanho', 'Variação/Cor/Tamanho',
        'Variacao/Cor/Tamanho', 'Variation', 'Opção', 'Opcao',
        'Especificação', 'variação', 'Atributo'
    ],
    'quantidade': [
        'Qtd. do Produto', 'Qtd do Produto', 'Quantidade', 'Qtd',
        'Qty', 'Quantity', 'qtd. do produto', 'Qtd. Produto',
        'Quantidade do Produto'
    ],
    'link_imagem': [
        'Link da Imagem', 'Imagem', 'URL da Imagem', 'Image URL',
        'Link Imagem', 'Foto', 'URL Imagem', 'link da imagem',
        'Imagem do Produto'
    ]
}


def encontrar_coluna(df_columns: list, possiveis: list) -> str | None:
    """Encontra a coluna correspondente no DataFrame."""
    for col in possiveis:
        if col in df_columns:
            return col
    # Tenta match parcial case-insensitive
    for col in possiveis:
        for df_col in df_columns:
            if col.lower() in df_col.lower() or df_col.lower() in col.lower():
                return df_col
    return None


def render():
    """Renderiza a página de importação de pedidos."""
    st.header("📦 Importação de Pedidos")
    st.caption("Faça upload da planilha de pedidos do UpSeller (formato .xlsx)")

    uploaded_file = st.file_uploader(
        "Selecione a planilha XLSX",
        type=["xlsx", "xls"],
        help="Planilha exportada do UpSeller com os pedidos do dia/lote"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.success(f"✅ Planilha carregada: {len(df)} linhas encontradas")

            # Mapear colunas
            colunas_encontradas = {}
            colunas_faltantes = []

            for campo, possiveis in COLUMN_MAP.items():
                col_encontrada = encontrar_coluna(df.columns.tolist(), possiveis)
                if col_encontrada:
                    colunas_encontradas[campo] = col_encontrada
                else:
                    colunas_faltantes.append(campo)

            # Mostrar mapeamento e permitir ajuste
            with st.expander("⚙️ Mapeamento de Colunas", expanded=bool(colunas_faltantes)):
                st.caption("Ajuste o mapeamento se a detecção automática não acertou.")
                todas_colunas = [""] + df.columns.tolist()

                for campo in COLUMN_MAP.keys():
                    default_idx = 0
                    if campo in colunas_encontradas:
                        try:
                            default_idx = todas_colunas.index(colunas_encontradas[campo])
                        except ValueError:
                            default_idx = 0

                    labels = {
                        'numero_pedido': 'Nº de Pedido',
                        'titulo_anuncio': 'Nome do Anúncio',
                        'sku': 'SKU',
                        'variacao': 'Variação/Cor/Tamanho',
                        'quantidade': 'Quantidade',
                        'link_imagem': 'Link da Imagem'
                    }

                    selecionada = st.selectbox(
                        f"Coluna para **{labels.get(campo, campo)}**",
                        options=todas_colunas,
                        index=default_idx,
                        key=f"map_{campo}"
                    )
                    if selecionada:
                        colunas_encontradas[campo] = selecionada

            # Verificação mínima
            campos_obrigatorios = ['numero_pedido', 'titulo_anuncio', 'quantidade']
            faltando = [c for c in campos_obrigatorios if c not in colunas_encontradas or not colunas_encontradas[c]]

            if faltando:
                st.warning(f"⚠️ Colunas obrigatórias não mapeadas: {', '.join(faltando)}")
                return

            # Preview dos dados com imagem
            st.subheader("👁️ Prévia dos Pedidos")

            for idx, row in df.iterrows():
                col_img, col_info = st.columns([1, 4])

                # Imagem do produto
                with col_img:
                    link_img = ""
                    if 'link_imagem' in colunas_encontradas and colunas_encontradas['link_imagem']:
                        link_img = str(row.get(colunas_encontradas['link_imagem'], ""))
                    if link_img and link_img != "nan" and link_img.startswith("http"):
                        try:
                            st.image(link_img, width=80)
                        except Exception:
                            st.write("📷 Sem foto")
                    else:
                        st.write("📷 Sem foto")

                # Info do pedido
                with col_info:
                    titulo = str(row.get(colunas_encontradas.get('titulo_anuncio', ''), 'N/A'))
                    pedido = str(row.get(colunas_encontradas.get('numero_pedido', ''), 'N/A'))
                    variacao = str(row.get(colunas_encontradas.get('variacao', ''), '')) if 'variacao' in colunas_encontradas else ''
                    sku = str(row.get(colunas_encontradas.get('sku', ''), '')) if 'sku' in colunas_encontradas else ''
                    qtd = row.get(colunas_encontradas.get('quantidade', ''), 1)

                    st.markdown(f"**{titulo}**")
                    st.caption(f"Pedido: {pedido} | SKU: {sku} | Variação: {variacao} | Qtd: {qtd}")

                st.divider()

                # Limitar preview
                if idx >= 19:
                    st.info(f"... e mais {len(df) - 20} itens")
                    break

            # Botão de importação
            st.divider()
            nome_lote = st.text_input(
                "Nome do Lote",
                value=f"Lote {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                help="Identificação do lote para referência futura"
            )

            if st.button("🚀 Importar Pedidos", type="primary", use_container_width=True):
                with st.spinner("Importando pedidos..."):
                    lote_id = db.criar_lote(nome_lote, uploaded_file.name)
                    importados = 0

                    for _, row in df.iterrows():
                        try:
                            pedido = str(row.get(colunas_encontradas.get('numero_pedido', ''), ''))
                            titulo = str(row.get(colunas_encontradas.get('titulo_anuncio', ''), ''))
                            sku = str(row.get(colunas_encontradas.get('sku', ''), '')) if 'sku' in colunas_encontradas else ''
                            variacao = str(row.get(colunas_encontradas.get('variacao', ''), '')) if 'variacao' in colunas_encontradas else ''
                            qtd = int(row.get(colunas_encontradas.get('quantidade', ''), 1) or 1)
                            link_img = str(row.get(colunas_encontradas.get('link_imagem', ''), '')) if 'link_imagem' in colunas_encontradas else ''

                            if link_img == 'nan':
                                link_img = ''
                            if sku == 'nan':
                                sku = ''
                            if variacao == 'nan':
                                variacao = ''

                            db.inserir_item_pedido(
                                lote_id=lote_id,
                                numero_pedido=pedido,
                                titulo_anuncio=titulo,
                                sku=sku,
                                variacao=variacao,
                                quantidade=qtd,
                                link_imagem=link_img
                            )
                            importados += 1
                        except Exception as e:
                            st.warning(f"⚠️ Erro na linha: {e}")

                    st.success(f"✅ {importados} itens importados no lote '{nome_lote}'!")
                    st.balloons()
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Erro ao ler planilha: {e}")

    # ------ Lotes importados ------
    st.divider()
    st.subheader("📁 Lotes Importados")
    lotes = db.listar_lotes()

    if lotes:
        for lote in lotes:
            itens = db.listar_itens_lote(lote['id'])
            n_associados = sum(1 for i in itens if i['associado'])
            with st.expander(
                f"📂 {lote['nome']} — {len(itens)} itens ({n_associados} associados) — {lote['data_importacao']}"
            ):
                for item in itens[:10]:
                    status = "✅" if item['associado'] else "⚠️"
                    st.write(f"{status} Pedido {item['numero_pedido']}: {item['titulo_anuncio']} ({item['variacao']}) x{item['quantidade']}")
                if len(itens) > 10:
                    st.caption(f"... e mais {len(itens) - 10} itens")
    else:
        st.info("Nenhum lote importado ainda.")
