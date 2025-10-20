import os
import unicodedata
import pandas as pd
import streamlit as st
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt


# Configuração inicial da página

st.set_page_config(
    page_title="InteliAgro",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded")

# 1. Carregamento ou criação da base de dados (OTIMIZADO)

CAMINHO_ARQUIVO = "cultivos_dados.csv"
CAMINHO_EXCEL = "Culturas_HecMunicípios.xlsx"


@st.cache_data(ttl=300)
def carregar_dados():
    if os.path.exists(CAMINHO_ARQUIVO):
        try:
            df = pd.read_csv(CAMINHO_ARQUIVO)
            colunas_necessarias = ["Cultura", "Pragas", "Defensivos", "Cidades", "Área total (ha)"]
            for coluna in colunas_necessarias:
                if coluna not in df.columns:
                    df[coluna] = ""
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return pd.DataFrame(columns=colunas_necessarias + ["Data Cadastro"])
    return pd.DataFrame(columns=["Cultura", "Pragas", "Defensivos", "Cidades", "Área total (ha)", "Data Cadastro"])


if "df" not in st.session_state:
    st.session_state.df = carregar_dados()
if "tema" not in st.session_state:
    st.session_state.tema = "Claro"
if "filtro_ativo" not in st.session_state:
    st.session_state.filtro_ativo = False
if "pragas_temp" not in st.session_state:
    st.session_state.pragas_temp = []
if "defensivos_temp" not in st.session_state:
    st.session_state.defensivos_temp = []

df = st.session_state.df


# 2. Funções utilitárias


def buscar_informacoes(termo, coluna_especifica=None):
    """Busca termo em todas as colunas ou em coluna específica do DataFrame."""
    if not termo.strip():
        return pd.DataFrame()

    termo = termo.strip().lower()

    if coluna_especifica and coluna_especifica in df.columns:
        return df[df[coluna_especifica].astype(str).str.lower().str.contains(termo, na=False)]
    else:
        return df[df.apply(lambda linha: linha.astype(str).str.lower().str.contains(termo).any(), axis=1)]


def salvar_dados():
    """Salva o DataFrame atual em CSV."""
    try:
        st.session_state.df.to_csv(CAMINHO_ARQUIVO, index=False)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")
        return False


def processar_lista_texto(texto):
    """Processa texto separado por vírgulas, removendo duplicatas e espaços extras."""
    if pd.isna(texto) or not texto.strip():
        return ""

    itens = [item.strip() for item in texto.split(",") if item.strip()]
    # Remove duplicatas mantendo a ordem
    itens_unicos = []
    for item in itens:
        if item not in itens_unicos:
            itens_unicos.append(item)

    return "\n".join(itens_unicos)


def formatar_lista_para_exibicao(texto, max_itens=15):
    """Formata texto separado por vírgulas para exibição compacta."""
    if pd.isna(texto) or not texto.strip():
        return "Nenhum item cadastrado"

    itens = [item.strip() for item in texto.split("\n") if item.strip()]

    if len(itens) <= max_itens:
        return "\n".join([f"• {item}" for item in itens])
    else:
        exibidos = itens[:max_itens]
        restantes = len(itens) - max_itens
        return "\n".join([f"• {item}" for item in exibidos]) + f"\n• ... e mais {restantes} itens"


def contar_itens_lista(texto):
    """Conta quantos itens existem em lista formatada."""
    if pd.isna(texto) or not texto.strip():
        return 0
    return len([item for item in texto.split("\n") if item.strip()])


def limpar_listas_temporarias():
    """Limpa as listas temporárias após o envio do formulário"""
    st.session_state.pragas_temp = []
    st.session_state.defensivos_temp = []


# 3. Sistema de temas e Sidebar

st.sidebar.title("⚙️ Configurações Avançadas")
tema_atual = st.sidebar.radio("🎨 Tema da Interface", ["Claro", "Escuro", "Natureza", "Profissional"],
                              index=["Claro", "Escuro", "Natureza", "Profissional"].index(st.session_state.tema))
st.session_state.tema = tema_atual

config_tema = {
    "Claro": {"fundo": "#fdfdfd",
              "texto": "#1b1b1b",
              "destaque": "#02735E",
              "secundario": "#254B20",
              "input_bg": "#f1f1f1",
              "card_bg": "#ffffff",
              "borda": "#e0e0e0"},
    "Escuro": {"fundo": "#0b0c10",
               "texto": "#f8f9fa",
               "destaque": "#07B3E0",
               "secundario": "#FFFFFF",
               "input_bg": "#1c1c1c",
               "card_bg": "#1f2833",
               "borda": "#2a2a2a"},
    "Natureza": {"fundo": "#f5f9f0",
                 "texto": "#2d5016",
                 "destaque": "#4a7c3a",
                 "secundario": "#8bb574",
                 "input_bg": "#ffffff",
                 "card_bg": "#e8f4e1",
                 "borda": "#c8e0b8"},
    "Profissional": {"fundo": "#f8fafc",
                     "texto": "#1e293b",
                     "destaque": "#3b82f6",
                     "secundario": "#64748b",
                     "input_bg": "#ffffff",
                     "card_bg": "#f1f5f9",
                     "borda": "#cbd5e1"}
}

cores = config_tema[st.session_state.tema]

st.sidebar.markdown("---")
exibicao_compacta = st.sidebar.checkbox("Modo de exibição compacta", value=True)
itens_por_pagina = st.sidebar.slider("Itens por página", 5, 40, 20)
mostrar_estatisticas = st.sidebar.checkbox("Mostrar estatísticas", value=True)


# 4. Interface principal

st.markdown(f"""
    <style>
    .main {{
        background-color: {cores['fundo']};
        color: {cores['texto']};
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}

    h1 {{
        color: {cores['destaque']};
        font-size: 2.5em !important;
        text-align: center;
        font-weight: 700;
        margin-bottom: 0.5em !important;
    }}

    h2, h3 {{
        color: {cores['secundario']};
        font-weight: 600 !important;
    }}

    .card {{
        background-color: {cores['card_bg']};
        border: 1px solid {cores['borda']};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .destaque-card {{
        background: linear-gradient(135deg, {cores['destaque']}20, {cores['secundario']}20);
        border-left: 4px solid {cores['destaque']};
    }}

    [data-testid="stSidebar"] {{
        background-color: {cores['card_bg']} !important;
    }}

    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
        font-size: 1.6em !important;
        font-weight: 700 !important;
        color: {cores['destaque']} !important;
        text-align: center !important;
        margin-top: 10px !important;
        margin-bottom: 15px !important;
    }}

    input, textarea, select {{
        background-color: {cores['input_bg']} !important;
        color: {cores['texto']} !important;
        border: 1px solid {cores['borda']} !important;
        border-radius: 8px !important;
        font-size: 14px !important;
    }}

    div.stButton > button {{
        background-color: {cores['secundario']};
        color: white;
        border-radius: 10px;
        font-size: 16px;
        font-weight: bold;
        height: 45px;
        width: 100%;
        transition: 0.3s;
        border: none;
    }}

    div.stButton > button:hover {{
        background-color: {cores['destaque']};
        color: {cores['fundo']};
        transform: scale(1.03);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}

    .streamlit-expanderHeader {{
        background-color: {cores['input_bg']} !important;
        color: {cores['texto']} !important;
        border-radius: 8px !important;
        border: 1px solid {cores['borda']} !important;
        font-weight: 600 !important;
    }}

    .streamlit-expanderContent {{
        background-color: {cores['card_bg']} !important;
        color: {cores['texto']} !important;
        border-radius: 0 0 8px 8px !important;
    }}

    .white-space-pre {{
        white-space: pre-wrap !important;
        line-height: 1.6 !important;
        font-family: 'Courier New', monospace;
    }}

    .metric-card {{
        background: linear-gradient(135deg, {cores['destaque']}15, {cores['secundario']}15);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid {cores['borda']};
    }}

    .tag {{
        display: inline-block;
        background-color: {cores['secundario']}30;
        color: {cores['secundario']};
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8em;
        margin: 0.1rem;
        border: 1px solid {cores['secundario']}50;
    }}

    .item-list {{
        background-color: {cores['input_bg']};
        border: 1px solid {cores['borda']};
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.3rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .delete-btn {{
        background-color: #ff4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 30px !important;
        height: 30px !important;
        padding: 0 !important;
        min-width: auto !important;
    }}

    .add-btn {{
        background-color: {cores['destaque']} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.3rem 1rem !important;
        margin-left: 0.5rem !important;
    }}

    footer {{visibility: hidden;}}

    /* Scrollbar personalizada */
    ::-webkit-scrollbar {{
        width: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: {cores['input_bg']};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {cores['secundario']};
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {cores['destaque']};
    }}
    </style>
""", unsafe_allow_html=True)


# 5. Interface principal

# Menu de navegação
menu = st.sidebar.radio("📋 Navegação",
                        ["Início", "Inserir Dados", "Consultar Informações", "Estatísticas", "Gerenciar Dados"])
# 5.1 Página Inicial
if menu == "Início":
    st.subheader("🏠 Bem-vindo ao InteliAgro")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h3>📊 Total de Culturas</h3>
            <h2>{len(df['Cultura'].unique()) if not df.empty else 0}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_area = df["Área total (ha)"].sum() if not df.empty else 0
        st.markdown(f"""
        <div class='metric-card'>
            <h3>🌍 Área Total</h3>
            <h2>{total_area:,.1f} ha</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        total_registros = len(df) if not df.empty else 0
        st.markdown(f"""
        <div class='metric-card'>
            <h3>📝 Registros</h3>
            <h2>{total_registros}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Culturas recentes (últimos 5 registros)
    if not df.empty:
        st.subheader("🌱 Culturas Recentes")
        dados_recentes = df.tail(5)

        for idx, linha in dados_recentes.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='card destaque-card'>
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h4 style="margin: 0; color: {cores['destaque']};">{linha['Cultura']}</h4>
                            <p style="margin: 0.2rem 0; font-size: 0.9em;">Área: {linha['Área total (ha)']:,.2f} ha</p>
                            <p style="margin: 0.2rem 0; font-size: 0.9em;">Cidades: {linha['Cidades']}</p>
                        </div>
                        <div style="text-align: right;">
                            <span class='tag'>{contar_itens_lista(linha['Pragas'])} pragas</span>
                            <span class='tag'>{contar_itens_lista(linha['Defensivos'])} defensivos</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("📝 Nenhum dado cadastrado ainda. Use a opção 'Inserir Dados' para começar.")


# 5.2 Inserção de Dados

elif menu == "Inserir Dados":
    st.subheader("📋 Cadastrar Nova Cultura")

    with st.form("form_insercao", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            cultura = st.text_input("🌱 Cultura *", placeholder="Ex: Soja, Milho, Café...")
            area = st.number_input("📏 Área total (ha) *", min_value=0.1, step=0.1, format="%.1f", value=1.0)
            cidades = st.text_area("🏙️ Cidades",
                                   placeholder="Separadas por vírgula\nEx: São Paulo, Campinas, Ribeirão Preto")

            # 🐛 ENTRADA DINÂMICA DE PRAGAS
            st.markdown("---")
            st.write("🐛 **Pragas**")

            # Input para adicionar pragas individualmente
            col_p1, col_p2 = st.columns([3, 1])
            with col_p1:
                praga_input = st.text_input("Nome da praga", placeholder="Ex: Mosca-branca", key="praga_input",
                                            label_visibility="collapsed")
            with col_p2:
                add_praga = st.form_submit_button("➕ Adicionar", use_container_width=True, key="add_praga")

            if add_praga and praga_input.strip():
                if praga_input.strip() not in st.session_state.pragas_temp:
                    st.session_state.pragas_temp.append(praga_input.strip())
                st.rerun()

            # Exibe pragas adicionadas com opção de remover
            if st.session_state.pragas_temp:
                st.write("**Pragas adicionadas:**")
                for i, praga in enumerate(st.session_state.pragas_temp):
                    col_p3, col_p4 = st.columns([4, 1])
                    with col_p3:
                        st.markdown(f"<div class='item-list'>🐛 {praga}</div>", unsafe_allow_html=True)
                    with col_p4:
                        if st.form_submit_button("❌", key=f"del_praga_{i}", use_container_width=True):
                            st.session_state.pragas_temp.pop(i)
                            st.rerun()
            else:
                st.info("ℹ️ Nenhuma praga adicionada")

            # Opção alternativa de entrada em lote
            with st.expander("📝 Ou digite várias pragas de uma vez"):
                pragas_lote = st.text_area("Pragas separadas por vírgula",
                                           placeholder="Mosca-branca, Lagarta, Ácaro...",
                                           key="pragas_lote")
                if st.form_submit_button("📥 Carregar Pragas do Lote", key="load_pragas", use_container_width=True):
                    if pragas_lote.strip():
                        novas_pragas = [p.strip() for p in pragas_lote.split(",") if p.strip()]
                        for praga in novas_pragas:
                            if praga not in st.session_state.pragas_temp:
                                st.session_state.pragas_temp.append(praga)
                        st.rerun()

        with col2:
            # 🧪 ENTRADA DINÂMICA DE DEFENSIVOS
            st.write("🧪 **Defensivos**")

            # Input para adicionar defensivos individualmente
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1:
                defensivo_input = st.text_input("Nome do defensivo", placeholder="Ex: Imidacloprido",
                                                key="defensivo_input", label_visibility="collapsed")
            with col_d2:
                add_defensivo = st.form_submit_button("➕ Adicionar", use_container_width=True, key="add_defensivo")

            if add_defensivo and defensivo_input.strip():
                if defensivo_input.strip() not in st.session_state.defensivos_temp:
                    st.session_state.defensivos_temp.append(defensivo_input.strip())
                st.rerun()

            # Exibe defensivos adicionados com opção de remover
            if st.session_state.defensivos_temp:
                st.write("**Defensivos adicionados:**")
                for i, defensivo in enumerate(st.session_state.defensivos_temp):
                    col_d3, col_d4 = st.columns([4, 1])
                    with col_d3:
                        st.markdown(f"<div class='item-list'>🧪 {defensivo}</div>", unsafe_allow_html=True)
                    with col_d4:
                        if st.form_submit_button("❌", key=f"del_defensivo_{i}", use_container_width=True):
                            st.session_state.defensivos_temp.pop(i)
                            st.rerun()
            else:
                st.info("ℹ️ Nenhum defensivo adicionado")

            # Opção alternativa de entrada em lote
            with st.expander("📝 Ou digite vários defensivos de uma vez"):
                defensivos_lote = st.text_area("Defensivos separados por vírgula",
                                               placeholder="Imidacloprido, Tiametoxam, Clorantraniliprole...",
                                               key="defensivos_lote")
                if st.form_submit_button("📥 Carregar Defensivos do Lote", key="load_defensivos",
                                         use_container_width=True):
                    if defensivos_lote.strip():
                        novos_defensivos = [d.strip() for d in defensivos_lote.split(",") if d.strip()]
                        for defensivo in novos_defensivos:
                            if defensivo not in st.session_state.defensivos_temp:
                                st.session_state.defensivos_temp.append(defensivo)
                        st.rerun()


        # Resumo antes do envio
        st.markdown("---")
        st.subheader("📋 Resumo do Cadastro")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.write(f"**Cultura:** {cultura if cultura.strip() else 'Não informada'}")
            st.write(f"**Área:** {area} ha")
            st.write(f"**Cidades:** {cidades if cidades.strip() else 'Não informadas'}")
        with col_r2:
            st.write(f"**Pragas:** {len(st.session_state.pragas_temp)}")
            st.write(f"**Defensivos:** {len(st.session_state.defensivos_temp)}")

        # Botão de envio
        col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
        with col_b2:
            submit = st.form_submit_button("💾 Salvar Cultura", use_container_width=True)

        if submit:
            if cultura.strip():
                # Prepara os dados das listas
                pragas_final = ", ".join(st.session_state.pragas_temp) if st.session_state.pragas_temp else ""
                defensivos_final = ", ".join(
                    st.session_state.defensivos_temp) if st.session_state.defensivos_temp else ""

                # Processa os dados
                novo_registro = {
                    "Cultura": cultura.strip(),
                    "Pragas": processar_lista_texto(pragas_final),
                    "Defensivos": processar_lista_texto(defensivos_final),
                    "Cidades": cidades.strip(),
                    "Área total (ha)": area,
                    "Data Cadastro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Adiciona ao DataFrame
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([novo_registro])], ignore_index=True)

                if salvar_dados():
                    st.success(f"✅ Cultura '{cultura}' cadastrada com sucesso!")
                    st.balloons()
                    # Limpa as listas temporárias
                    limpar_listas_temporarias()
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar os dados.")
            else:
                st.error("⚠️ O campo 'Cultura' é obrigatório.")

# 5.3 Consulta de Dados

elif menu == "Consultar Informações":
    st.subheader("🔍 Busca Avançada")

    # Filtros avançados
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        termo_geral = st.text_input("🔎 Buscar em todos os campos",
                                    placeholder="Digite um termo...")

    with col_f2:
        coluna_filtro = st.selectbox("Filtrar por coluna específica",
                                     ["Todas as colunas", "Cultura", "Pragas", "Defensivos", "Cidades"])

    with col_f3:
        if not df.empty:
            cultura_filtro = st.multiselect("Filtrar por cultura",
                                            options=df['Cultura'].unique(),
                                            placeholder="Selecione culturas...")

    # Aplicar filtros
    resultados = df.copy()

    if termo_geral.strip():
        coluna = None if coluna_filtro == "Todas as colunas" else coluna_filtro
        resultados = buscar_informacoes(termo_geral, coluna)
        st.session_state.filtro_ativo = True

    if cultura_filtro and not df.empty:
        resultados = resultados[resultados['Cultura'].isin(cultura_filtro)]
        st.session_state.filtro_ativo = True

    # Exibir resultados
    if not termo_geral.strip() and not cultura_filtro:
        st.info("💡 Use os filtros acima para buscar informações.")
        resultados = pd.DataFrame()  # Não mostrar todos inicialmente
        st.session_state.filtro_ativo = False

    if st.session_state.filtro_ativo and resultados.empty:
        st.warning("❌ Nenhum registro encontrado com os filtros aplicados.")

    elif not resultados.empty:
        st.success(f"✅ {len(resultados)} registro(s) encontrado(s).")

        # Controles de paginação
        total_paginas = max(1, (len(resultados) + itens_por_pagina - 1) // itens_por_pagina)
        if total_paginas > 1:
            pagina = st.number_input("📄 Página", min_value=1, max_value=total_paginas, value=1)
            inicio = (pagina - 1) * itens_por_pagina
            fim = min(pagina * itens_por_pagina, len(resultados))
            resultados_pagina = resultados.iloc[inicio:fim]
            st.caption(f"Mostrando {inicio + 1}-{fim} de {len(resultados)} registros")
        else:
            resultados_pagina = resultados

        # Exibir resultados
        for idx, linha in resultados_pagina.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='card'>
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                        <div>
                            <h3 style="margin: 0; color: {cores['destaque']};">{linha['Cultura']}</h3>
                            <p style="margin: 0.2rem 0; font-size: 0.9em; color: {cores['secundario']};">📏 
{linha['Área total (ha)']:,.2f} ha | 🏙️ {linha['Cidades']}</p>
                        </div>
                        <div style="text-align: right;">
                            <span class='tag'>🐛 {contar_itens_lista(linha['Pragas'])}</span>
                            <span class='tag'>🧪 {contar_itens_lista(linha['Defensivos'])}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_d1, col_d2 = st.columns(2)

                with col_d1:
                    with st.expander(f"🐛 Pragas ({contar_itens_lista(linha['Pragas'])})", expanded=False):
                        if contar_itens_lista(linha['Pragas']) > 0:
                            st.text(formatar_lista_para_exibicao(linha['Pragas']))
                        else:
                            st.info("Nenhuma praga cadastrada")

                with col_d2:
                    with st.expander(f"🧪 Defensivos ({contar_itens_lista(linha['Defensivos'])})", expanded=False):
                        if contar_itens_lista(linha['Defensivos']) > 0:
                            st.text(formatar_lista_para_exibicao(linha['Defensivos']))
                        else:
                            st.info("Nenhum defensivo cadastrado")


                st.markdown("---")

        # Estatísticas dos resultados
        if mostrar_estatisticas:
            with st.expander("📊 Estatísticas dos Resultados", expanded=False):
                col_s1, col_s2, col_s3 = st.columns(3)


                def normalizar_texto(texto):
                    """Remove acentos e converte para minúsculas."""
                    if pd.isna(texto):
                        return ""
                    texto = str(texto).strip().lower()
                    texto = "".join(
                        c for c in unicodedata.normalize("NFD", texto)
                        if unicodedata.category(c) != "Mn"
                    )
                    return texto


                try:
                    caminho_excel = "Culturas_HecMunicípios.xlsx"
                    if os.path.exists(caminho_excel):
                        df_excel = pd.read_excel(caminho_excel)

                        # Detecta colunas
                        cidade_col = next((c for c in df_excel.columns if "cidade" in c.lower()), None)
                        area_col = next((c for c in df_excel.columns if "hect" in c.lower() or "área" in c.lower()),
                                        None)
                        cultura_col = next(
                            (c for c in df_excel.columns if "cultura" in c.lower() or "cultivo" in c.lower()), None)

                        if cidade_col and area_col:
                            st.markdown("### 🏙️ Cidades e Hectares (Filtradas pela Cultura)")

                            df_cidades = df_excel.copy()
                            colunas_padrao = {}
                            if cultura_col:
                                colunas_padrao[cultura_col] = "Cultura"
                            colunas_padrao[cidade_col] = "Cidade"
                            colunas_padrao[area_col] = "Área (ha)"
                            df_cidades.rename(columns=colunas_padrao, inplace=True)

                            # Normalização
                            df_cidades["Cidade_norm"] = df_cidades["Cidade"].apply(normalizar_texto)
                            if "Cultura" in df_cidades.columns:
                                df_cidades["Cultura_norm"] = df_cidades["Cultura"].apply(normalizar_texto)
                            df_cidades["Área (ha)"] = pd.to_numeric(df_cidades["Área (ha)"], errors="coerce").fillna(0)

                            # Filtro robusto
                            if not resultados.empty and "Cultura" in resultados.columns:
                                culturas_ativas = [normalizar_texto(c) for c in resultados["Cultura"].unique()]

                                if "Cultura_norm" in df_cidades.columns:
                                    filtro = df_cidades["Cultura_norm"].apply(
                                        lambda x: any(cultura in x or x in cultura for cultura in culturas_ativas)
                                    )
                                else:
                                    filtro = pd.Series([True] * len(df_cidades))
                            else:
                                filtro = pd.Series([True] * len(df_cidades))

                            df_filtrado = df_cidades[filtro]

                            # Exibe resultados
                            if not df_filtrado.empty:
                                st.dataframe(
                                    df_filtrado[["Cidade", "Área (ha)"]],
                                    use_container_width=True,
                                )
                                st.caption(f"Mostrando {len(df_filtrado)} cidade(s) correspondentes.")
                            else:
                                st.info(
                                    "ℹ️ Nenhuma cidade correspondente à cultura pesquisada foi encontrada no Excel.")
                        else:
                            st.warning("⚠️ Colunas de cidade ou hectares não foram encontradas no arquivo Excel.")
                    else:
                        st.info("ℹ️ Arquivo 'Culturas_Áreas_Municípios.xlsx' não encontrado no diretório atual.")
                except Exception as e:
                    st.error(f"Erro ao carregar dados do Excel: {e}")

            with col_s1:
                area_total = resultados["Área total (ha)"].sum()
                st.metric("Área Total", f"{area_total:,.2f} ha")

            with col_s2:
                culturas_unicas = len(resultados['Cultura'].unique())
                st.metric("Culturas Únicas", culturas_unicas)

            with col_s3:
                media_area = resultados["Área total (ha)"].mean()
                st.metric("Área Média", f"{media_area:,.2f} ha")


# 6. Estatísticas

if menu == "Estatísticas":
    st.subheader("📊 Estatísticas Completas")

    if df.empty:
        st.info("📝 Nenhum dado disponível para análise.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Visão Geral", "🏙️ Por Localização", "🧪 Defensivos Agrícolas", "🐛 Pragas"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total de Registros", len(df))
                st.metric("Culturas Únicas", len(df['Cultura'].unique()))
                total_pragas = sum(contar_itens_lista(pragas) for pragas in df['Pragas'])
                st.metric("Total de Pragas Catalogadas", total_pragas)
            with col2:
                area_total = df["Área total (ha)"].sum()
                st.metric("Área Total Cultivada", f"{area_total:,.1f} ha")
                area_media = df["Área total (ha)"].mean()
                st.metric("Área Média por Cultura", f"{area_media:,.1f} ha")
                total_defensivos = sum(contar_itens_lista(defensivos) for defensivos in df['Defensivos'])
                st.metric("Total de Defensivos Catalogados", total_defensivos)

        with tab2:
            todas_cidades = [cidade.strip() for cidades in df['Cidades'].dropna() for cidade in cidades.split(',') if cidade.strip()]
            contagem_cidades = Counter(todas_cidades)
            if contagem_cidades:
                cidades_comuns = contagem_cidades.most_common(10)
                st.markdown("### 🏙️ Cidades mais frequentes")
                for cidade, count in cidades_comuns:
                    st.markdown(f"- **{cidade}** — {count} ocorrência(s)")

        with tab3:
            st.subheader("🧪 Estatísticas de Defensivos Agrícolas")
            if df.empty or df['Defensivos'].dropna().eq("").all():
                st.info("ℹ️ Nenhum defensivo agrícola cadastrado na base.")
            else:
                defensivos_list = [d.strip() for texto in df['Defensivos'].dropna() for d in texto.replace("\n", ",").split(",") if d.strip()]
                contagem_defensivos = Counter(defensivos_list)
                total_defensivos = len(contagem_defensivos)
                st.metric("Total de Defensivos Únicos", total_defensivos)
                st.markdown("### 🔝 Defensivos mais utilizados")
                defensivos_ordenados = sorted(contagem_defensivos.items(), key=lambda x: x[1], reverse=True)
                for nome, qtd in defensivos_ordenados:
                    st.markdown(f"- **{nome}** — {qtd} ocorrência(s)")
                top_n = min(10, len(defensivos_ordenados))


        with tab4:
            st.subheader("🐛 Pragas mais Frequentes")
            if df.empty or df['Pragas'].dropna().eq("").all():
                st.info("ℹ️ Nenhuma praga cadastrada na base.")
            else:
                pragas_list = [p.strip() for texto in df['Pragas'].dropna() for p in texto.replace("\n", ",").split(",") if p.strip()]
                contagem_pragas = Counter(pragas_list)
                total_pragas = len(contagem_pragas)
                st.metric("Total de Pragas Únicas", total_pragas)
                st.markdown("### 🔝 Pragas mais frequentes")
                pragas_ordenadas = sorted(contagem_pragas.items(), key=lambda x: x[1], reverse=True)
                for nome, qtd in pragas_ordenadas:
                    st.markdown(f"- **{nome}** — {qtd} ocorrência(s)")
                top_n = min(10, len(pragas_ordenadas))



# 7. Gerenciar Dados

elif menu == "Gerenciar Dados":
    st.subheader("🗃️ Gerenciamento de Dados")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("### 💾 Backup de Dados")

        if not df.empty:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Baixar Base Completa (CSV)",
                csv,
                f"base_agricola_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                help="Baixe toda a base de dados em formato CSV",
                use_container_width=True
            )
        else:
            st.warning("Nenhum dado para exportar.")

    with col_g2:
        st.markdown("### ⚠️ Ações Administrativas")

        if st.button("🔄 Recarregar Dados", use_container_width=True):
            st.session_state.df = carregar_dados()
            st.rerun()

        if st.button("🧹 Limpar Filtros", use_container_width=True):
            st.session_state.filtro_ativo = False
            st.rerun()

        if st.button("🗑️ Limpar Listas Temporárias", use_container_width=True):
            limpar_listas_temporarias()
            st.success("Listas temporárias limpas!")
            st.rerun()



# 8. Rodapé

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
    "🌾 InteliAgro • Desenvolvido para ajudar e otimizar a agricultura"
    "</div>",
    unsafe_allow_html=True)
