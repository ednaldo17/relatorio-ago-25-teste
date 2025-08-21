import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard Rádio Bitury FM 98.3",
    page_icon="📻",
    layout="wide",
)

# --- Estilo Customizado ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1c1c1c, #3a3a3a);
        color: #f5f5f5;
        font-family: 'Arial', sans-serif;
    }

    h1, h2, h3 {
        color: #C55A2B !important;
        text-shadow: 1px 1px 3px #000;
    }

    .stMetric {
        background: #222;
        padding: 12px;
        border-radius: 12px;
        border: 1px solid #C55A2B;
        box-shadow: 0px 0px 8px #C55A2B;
    }

    section[data-testid="stSidebar"] {
        background-color: #111;
        color: white;
        border-right: 2px solid #C55A2B;
    }

    .stDataFrame {
        background-color: #1e1e1e;
    }
    </style>
""", unsafe_allow_html=True)

# --- Banner ---
st.markdown(
    """
    <div style='text-align: center; padding: 15px; 
                background: #111; border-radius: 15px; 
                margin-bottom: 25px;'>
        <h1>📻 Dashboard Rádio Bitury FM 98.3</h1>
        <p style='color: #C55A2B; font-size:18px;'>Monitoramento de campanhas e clientes no ar</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Carregamento dos Dados ---
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
            st.error(f"Erro: colunas {', '.join(colunas_faltando)} não encontradas.")
            return None

        df = df.rename(columns={v: k for k, v in mapa_colunas.items()})
        df['data_inicio'] = pd.to_datetime(df['data_inicio'], format='%d/%m/%Y', errors='coerce')
        df['data_fim'] = pd.to_datetime(df['data_fim'], format='%d/%m/%Y', errors='coerce')
        df['entrou'] = df['entrou'].str.strip().str.capitalize()
        df['saiu'] = df['saiu'].str.strip().str.capitalize()
        return df
    except FileNotFoundError:
        st.error("Erro: Arquivo CSV não encontrado.")
        return None

df = carregar_dados()
if df is None:
    st.stop()

# --- Filtros ---
st.sidebar.header("🔍 Filtros")
clientes_disponiveis = sorted(df['cliente'].unique())
clientes_selecionados = st.sidebar.multiselect("🎤 Cliente", clientes_disponiveis, default=clientes_disponiveis)
agencias_disponiveis = sorted(df['agencia'].dropna().unique())
agencias_selecionadas = st.sidebar.multiselect("🏢 Agência", agencias_disponiveis, default=agencias_disponiveis)

df_filtrado = df[
    (df['cliente'].isin(clientes_selecionados)) &
    (df['agencia'].isin(agencias_selecionadas) | df['agencia'].isna())
]

# --- Métricas ---
st.subheader("📊 Painel de Controle das Inserções")
df_agregado = df_filtrado.groupby('cliente').agg(Inserções=('insercoes', 'sum')).reset_index()

if not df_agregado.empty:
    media_insercoes = df_agregado['Inserções'].mean()
    total_insercoes = df_agregado['Inserções'].sum()
    total_clientes = df_agregado['cliente'].nunique()
    cliente_mais_frequente = df_agregado.loc[df_agregado['Inserções'].idxmax()]['cliente']
else:
    media_insercoes, total_insercoes, total_clientes, cliente_mais_frequente = 0, 0, 0, "Nenhum"

def formatar_numero(num): return f"{num:,.0f}".replace(',', '.')

col1, col2, col3, col4 = st.columns(4)
col1.metric("📡 Média por Cliente", formatar_numero(media_insercoes))
col2.metric("🎶 Total de Inserções", formatar_numero(total_insercoes))
col3.metric("👥 Total de Clientes", formatar_numero(total_clientes))
col4.metric("⭐ Cliente Destaque", cliente_mais_frequente)

# --- Tabela de Médias (Mensal e Diária) ---
st.markdown("---")
st.subheader("📅 Média de Inserções por Cliente (Diária e Mensal)")

df_medias = df_filtrado.copy()

# Garante datas válidas
df_medias['data_inicio'] = pd.to_datetime(df_medias['data_inicio'], errors='coerce')
df_medias['data_fim'] = pd.to_datetime(df_medias['data_fim'], errors='coerce')

# Define a data final como hoje, caso esteja vazia
df_medias['data_fim'] = df_medias['data_fim'].fillna(pd.Timestamp.today())

# Calcula duração em dias
df_medias['dias'] = (df_medias['data_fim'] - df_medias['data_inicio']).dt.days
df_medias['dias'] = df_medias['dias'].clip(lower=1)  # evita divisão por zero

# Médias
df_medias['Média Diária'] = df_medias['insercoes'] / df_medias['dias']
df_medias['Média Mensal'] = df_medias['insercoes'] / (df_medias['dias'] / 30)

# Agregar por cliente
df_medias_agg = df_medias.groupby('cliente').agg(
    Inserções_Totais=('insercoes', 'sum'),
    Média_Diária=('Média Diária', 'mean'),
    Média_Mensal=('Média Mensal', 'mean')
).reset_index()

# Formatação
df_medias_agg['Média_Diária'] = df_medias_agg['Média_Diária'].round(2)
df_medias_agg['Média_Mensal'] = df_medias_agg['Média_Mensal'].round(2)

# Exibir
st.dataframe(
    df_medias_agg.rename(columns={
        'cliente': 'Cliente',
        'Inserções_Totais': 'Inserções Totais',
        'Média_Diária': 'Média Diária',
        'Média_Mensal': 'Média Mensal'
    }),
    hide_index=True,
    use_container_width=True
)

# --- Tabela ---
st.markdown("---")
st.subheader("🎧 Comerciais no Ar")
st.dataframe(
    df_filtrado[['id', 'codigo', 'cliente', 'agencia', 'insercoes']].rename(columns={
        'id': 'ID', 'codigo': 'Código', 'cliente': 'Cliente', 'agencia': 'Agência', 'insercoes': 'Inserções'
    }),
    hide_index=True, use_container_width=True
)

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
            st.markdown(f"- 🎙 **{row['cliente']}** (Início: {row['data_inicio'].strftime('%d/%m/%Y') if pd.notna(row['data_inicio']) else 'Data não informada'})")

with col_saiu:
    st.markdown("#### ❌ Saíram do Ar")
    if df_saiu.empty:
        st.info("Nenhum cliente saiu este mês.")
    else:
        for _, row in df_saiu.iterrows():
            st.markdown(f"- 📻 **{row['cliente']}** (Fim: {row['data_fim'].strftime('%d/%m/%Y') if pd.notna(row['data_fim']) else 'Data não informada'})")

# --- Gráficos ---
st.markdown("---")
st.subheader("📊 Frequência Visual")

col_graf1, col_graf2 = st.columns(2)
if not df_agregado.empty:
    top_clientes = df_agregado.nlargest(15, 'Inserções').sort_values(by='Inserções', ascending=True)
    grafico_clientes = px.bar(
        top_clientes, x='Inserções', y='cliente', orientation='h',
        title="Top 15 Clientes no Ar",
        labels={'Inserções': 'Inserções', 'cliente': ''},
        text='Inserções',
        color='Inserções',
        color_continuous_scale=['#C55A2B', '#FF9E57']
    )
    grafico_clientes.update_layout(title_x=0.2, yaxis={'categoryorder':'total ascending'})
    col_graf1.plotly_chart(grafico_clientes, use_container_width=True)

    grafico_dist = px.pie(
        df_agregado.nlargest(10, 'Inserções'),
        names='cliente', values='Inserções',
        title='Distribuição de Inserções (Top 10)',
        hole=0.4,
        color_discrete_sequence=['#C55A2B', '#FF9E57', '#FFB07C', '#222']
    )
    grafico_dist.update_traces(textinfo='percent+label', textposition='inside')
    grafico_dist.update_layout(showlegend=False, title_x=0.15)
    col_graf2.plotly_chart(grafico_dist, use_container_width=True)



