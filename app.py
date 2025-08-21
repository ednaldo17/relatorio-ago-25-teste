import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Inserções de Rádio",
    page_icon="📻",
    layout="wide",
)

# --- Estilo Customizado (CSS) ---
st.markdown("""
    <style>
    /* Fundo com gradiente lembrando rádio */
    .stApp {
        background: linear-gradient(135deg, #1c1c1c, #3a3a3a);
        color: #f5f5f5;
        font-family: 'Arial', sans-serif;
    }
    
    /* Títulos com estilo neon */
    h1, h2, h3 {
        color: #FFD700 !important;
        text-shadow: 1px 1px 5px #ff6600;
    }

    /* Caixas de métricas com estilo de "painel digital" */
    .stMetric {
        background: #222;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #FFD700;
        box-shadow: 0px 0px 8px #ffcc00;
    }

    /* Sidebar com destaque */
    section[data-testid="stSidebar"] {
        background-color: #111;
        color: white;
        border-right: 2px solid #FFD700;
    }

    /* Tabela com estilo */
    .stDataFrame {
        background-color: #1e1e1e;
    }
    </style>
""", unsafe_allow_html=True)

# --- Banner Superior ---
st.markdown("""
    <div style='text-align: center; padding: 15px; 
                background: #111; border-radius: 15px; 
                margin-bottom: 25px; 
                box-shadow: 0px 0px 12px #FFD700;'>
        <h1>📻 Dashboard de Inserções de Rádio</h1>
        <p style='color: #FFD700; font-size:18px;'>Monitoramento de campanhas e clientes no ar!</p>
    </div>
""", unsafe_allow_html=True)

# --- Carregamento e Preparação dos Dados ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("relatorio AGO teste.csv")

        mapa_colunas = {
            "id": "ID",
            "codigo": "Código",
            "cliente": "Cliente",
            "agencia": "Agência",
            "insercoes": "Inserções",
            "entrou": "Entrou?",
            "data_inicio": "Data_Início",
            "saiu": "Saiu?",
            "data_fim": "Data_Fim"
        }

        colunas_necessarias = list(mapa_colunas.values())
        colunas_faltando = [col for col in colunas_necessarias if col not in df.columns]

        if colunas_faltando:
            st.error(
                f"Erro de Mapeamento: As colunas **{', '.join(colunas_faltando)}** não foram encontradas. "
                f"Corrija os nomes na seção 'MAPEAMENTO DE COLUNAS' do código."
            )
            return None

        mapa_rename_inverso = {v: k for k, v in mapa_colunas.items()}
        df = df.rename(columns=mapa_rename_inverso)

        df['data_inicio'] = pd.to_datetime(df['data_inicio'], format='%d/%m/%Y', errors='coerce')
        df['data_fim'] = pd.to_datetime(df['data_fim'], format='%d/%m/%Y', errors='coerce')

        df['entrou'] = df['entrou'].str.strip().str.capitalize()
        df['saiu'] = df['saiu'].str.strip().str.capitalize()

        return df
    except FileNotFoundError:
        st.error("Erro: O arquivo 'relatorio AGO teste.csv' não foi encontrado.")
        return None

df = carregar_dados()
if df is None:
    st.stop()

# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros de Transmissão")

clientes_disponiveis = sorted(df['cliente'].unique())
clientes_selecionados = st.sidebar.multiselect("🎤 Cliente", clientes_disponiveis, default=clientes_disponiveis)

agencias_disponiveis = sorted(df['agencia'].dropna().unique())
agencias_selecionadas = st.sidebar.multiselect("🏢 Agência", agencias_disponiveis, default=agencias_disponiveis)

# --- Filtragem ---
df_filtrado = df[
    (df['cliente'].isin(clientes_selecionados)) &
    (df['agencia'].isin(agencias_selecionadas) | df['agencia'].isna())
]

# --- Conteúdo Principal ---
st.subheader("📊 Painel de Controle das Inserções")

df_agregado = df_filtrado.groupby('cliente').agg(
    Inserções=('insercoes', 'sum')
).reset_index()

if not df_agregado.empty:
    media_insercoes = df_agregado['Inserções'].mean()
    total_insercoes = df_agregado['Inserções'].sum()
    total_clientes = df_agregado['cliente'].nunique()
    cliente_mais_frequente = df_agregado.loc[df_agregado['Inserções'].idxmax()]['cliente']
else:
    media_insercoes, total_insercoes, total_clientes, cliente_mais_frequente = 0, 0, 0, "Nenhum"

def formatar_numero(num):
    return f"{num:,.0f}".replace(',', '.')

col1, col2, col3, col4 = st.columns(4)
col1.metric("📡 Média por Cliente", formatar_numero(media_insercoes))
col2.metric("🎶 Total de Inserções", formatar_numero(total_insercoes))
col3.metric("👥 Total de Clientes", formatar_numero(total_clientes))
col4.metric("⭐ Cliente Destaque", cliente_mais_frequente)

# --- Tabela ---
st.markdown("---")
st.subheader("🎧 Lista Geral de Comerciais no Ar")

colunas_tabela_geral = ['id', 'codigo', 'cliente', 'agencia', 'insercoes']
df_tabela_geral = df_filtrado[colunas_tabela_geral].rename(columns={
    'id': 'ID',
    'codigo': 'Código',
    'cliente': 'Cliente',
    'agencia': 'Agência',
    'insercoes': 'Inserções'
})
st.dataframe(df_tabela_geral, hide_index=True, use_container_width=True)

# --- Movimentações ---
st.markdown("---")
st.subheader("📡 Movimentações de Clientes")

col_entrou, col_saiu = st.columns(2)
df_entrou = df_filtrado[df_filtrado['entrou'] == 'Sim']
df_saiu = df_filtrado[df_filtrado['saiu'] == 'Sim']

with col_entrou:
    st.markdown("#### ✅ Entraram no Ar")
    if df_entrou.empty:
        st.info("Nenhum cliente novo este mês.")
    else:
        for _, row in df_entrou.iterrows():
            data_formatada = row['data_inicio'].strftime('%d/%m/%Y') if pd.notna(row['data_inicio']) else 'Data não informada'
            st.markdown(f"- 🎙 **{row['cliente']}** (Início: {data_formatada})")

with col_saiu:
    st.markdown("#### ❌ Saíram do Ar")
    if df_saiu.empty:
        st.info("Nenhum cliente saiu este mês.")
    else:
        for _, row in df_saiu.iterrows():
            data_formatada = row['data_fim'].strftime('%d/%m/%Y') if pd.notna(row['data_fim']) else 'Data não informada'
            st.markdown(f"- 📻 **{row['cliente']}** (Fim: {data_formatada})")

# --- Gráficos ---
st.markdown("---")
st.subheader("📊 Frequência Visual")

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_agregado.empty:
        top_clientes = df_agregado.nlargest(15, 'Inserções').sort_values(by='Inserções', ascending=True)
        grafico_clientes = px.bar(
            top_clientes, x='Inserções', y='cliente', orientation='h',
            title="Top 15 Clientes no Ar",
            labels={'Inserções': 'Quantidade de Inserções', 'cliente': ''},
            text='Inserções',
            color='Inserções',
            color_continuous_scale='Oranges'
        )
        grafico_clientes.update_layout(title_x=0.2, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(grafico_clientes, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir.")

with col_graf2:
    if not df_agregado.empty and df_agregado['Inserções'].sum() > 0:
        grafico_dist = px.pie(
            df_agregado.nlargest(10, 'Inserções'),
            names='cliente', values='Inserções',
            title='Proporção de Inserções (Top 10)',
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Oranges
        )
        grafico_dist.update_traces(textinfo='percent+label', textposition='inside')
        grafico_dist.update_layout(showlegend=False, title_x=0.15)
        st.plotly_chart(grafico_dist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir.")
