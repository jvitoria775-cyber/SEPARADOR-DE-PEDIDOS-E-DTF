# ✨ Gratitude Têxtil — Sistema de Gestão de Pedidos & Produção DTF

Sistema interno para gestão, separação de pedidos e controle de produção de estampas DTF a partir de planilhas exportadas do UpSeller (Shopee, TikTok Shop, Shein, Mercado Livre, etc.).

---

## 🚀 Funcionalidades

1. **📦 Importação de Pedidos (UpSeller XLSX):**
   - Upload de planilhas de pedidos com auto-detecção de colunas.
   - Pré-visualização com fotos dos produtos ao lado do título.
   - Organização em lotes.

2. **📋 Cadastro de Produtos Base:**
   - Cadastro de produtos-mãe (Camiseta, Short Tactel, Baby Look, Cropped, etc.).
   - Definição de cores e grade de tamanhos em ordem progressiva fixa: `P, M, G, GG, G1, G2, G3, G4, G5`.

3. **🔗 Associação De/Para Inteligente (Memória Permanente):**
   - Mapeamento de kits (ex: Kit 3 Shorts = 3 unidades em tamanhos/cores configuráveis).
   - **Vínculo com 1 clique:** Se o anúncio for o mesmo produto de outro já cadastrado (mesmo com título diferente), basta selecionar e vincular em um único clique.
   - Salvo permanentemente no banco SQLite: anúncios já associados nunca mais pedem associação novamente.

4. **📝 Lista de Separação (Packing List):**
   - Formato limpo e direto estilo bloco de notas:
     ```text
     CAMISETA
     
     PRETO P 1
     PRETO M 2
     BRANCO G 1
     
     TOTAL: 4 PEÇAS
     ```
   - Download imediato em arquivo `.txt`.
   - **Descartável:** Após separar os pedidos, botão para concluir o lote e limpar a tela.

5. **🖨️ Produção DTF (Lista de Impressão Acumulativa):**
   - Unificação de anúncios com títulos diferentes que utilizam a mesma estampa de referência.
   - Soma automática de quantidades de impressões necessárias.
   - Controle de impressão com botão **"✅ Impresso"** e opção de limpar itens já impressos.
   - Exportação em `.csv`.

---

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10+
- **Frontend / Interface:** [Streamlit](https://streamlit.io/)
- **Banco de Dados:** SQLite (arquivo local em `data/pedidos.db`)
- **Processamento de Planilhas:** pandas & openpyxl

---

## 💻 Como Rodar o Projeto

1. Clone o repositório ou baixe os arquivos:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd "PROJETO SEPARAR PEDIDOS E DTF"
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Inicie o sistema:
   ```bash
   streamlit run app.py
   ```

4. Acesse no navegador:
   ```
   http://localhost:8501
   ```

---

Desenvolvido para **Gratitude Têxtil**.
