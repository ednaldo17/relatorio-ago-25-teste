import streamlit as st
import pandas as pd
import numpy as np # Adicionado para usar a função np.where
import plotly.express as px
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Inserções de Rádio",
    page_icon="📻",
    layout="wide",
)

# --- Carregamento e Preparação dos Dados ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("relatorio MAI.csv")
        df['Data_Inicio'] = pd.to_datetime(df['Data_Inicio'], errors='coerce')
        df['Data_Fim'] = pd.to_datetime(df['Data_Fim'], errors='coerce')

        # --- LÓGICA PARA AS NOVAS COLUNAS ---
        # Identifica o mês e ano atuais para a verificação
        data_atual = datetime.now()
        mes_atual = data_atual.month
        ano_atual = data_atual.year

        # 1. Cria a coluna "Entrou?"
        condicao_entrou = (df['Data_Inicio'].dt.month == mes_atual) & (df['Data_Inicio'].dt.year == ano_atual)
        df['Entrou?'] = np.where(condicao_entrou, 'Sim', 'Não')

        # 2. Cria a coluna "Saiu?"
        condicao_saiu = (df['Data_Fim'].dt.month == mes_atual) & (df['Data_Fim'].dt.year == ano_atual)
        df['Saiu?'] = np.where(condicao_saiu, 'Sim', 'Não')

        # 3. Cria a coluna "Data de Entrada" (condicional)
        # Preenche com a Data_Inicio se Entrou? for 'Sim', senão deixa vazio (NaT)
        df['Data de Entrada'] = np.where(df['Entrou?'] == 'Sim', df['Data_Inicio'], pd.NaT)

        # 4. Cria a coluna "Data de Saída" (condicional)
        # Preenche com a Data_Fim se Saiu? for 'Sim', senão deixa vazio (NaT)
        df['Data de Saída'] = np.where(df['Saiu?'] == 'Sim', df['Data_Fim'], pd.NaT)

        return df
    except FileNotFoundError:
        return None

df = carregar_dados()

if df is None:
    st.error("Erro: O arquivo 'relatorio MAI.csv' não foi encontrado. Certifique-se de que ele está na mesma pasta que o script.")
    st.stop()

# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros")

# Filtro de Cliente
clientes_disponiveis = sorted(df['Cliente'].unique())
clientes_selecionados = st.sidebar.multiselect("Cliente", clientes_disponiveis, default=clientes_disponiveis)

# Filtro de Agência
agencias_disponiveis = sorted(df['Agência'].dropna().unique())
agencias_selecionadas = st.sidebar.multiselect("Agência", agencias_disponiveis, default=agencias_disponiveis)

# --- Filtragem do DataFrame ---
df_filtrado = df[
    (df['Cliente'].isin(clientes_selecionados)) &
    (df['Agência'].isin(agencias_selecionadas) | df['Agência'].isna())
]

# Agrega os dados para as métricas e gráficos (soma as inserções por cliente)
df_agregado = df_filtrado.groupby('Cliente').agg(
    Inserções=('Inserções', 'sum')
).reset_index()

# --- Conteúdo Principal ---
st.title("📊 Dashboard de Análise de Inserções")
st.markdown("Explore os dados de inserções de comerciais. Utilize os filtros à esquerda para refinar sua análise.")

# --- Métricas Principais (KPIs) ---
st.markdown("---")
st.subheader("Métricas Gerais (com base nos filtros)")

if not df_agregado.empty:
    media_insercoes = df_agregado['Inserções'].mean()
    total_insercoes = df_agregado['Inserções'].sum()
    total_clientes = df_agregado['Cliente'].nunique()
    cliente_mais_frequente = df_agregado.loc[df_agregado['Inserções'].idxmax()]['Cliente']
else:
    media_insercoes, total_insercoes, total_clientes, cliente_mais_frequente = 0, 0, 0, "Nenhum"

def formatar_numero(num):
    return f"{num:,.0f}".replace(',', '.')

col1, col2, col3, col4 = st.columns(4)
col1.metric("Média de Inserções por Cliente", formatar_numero(media_insercoes))
col2.metric("Total de Inserções", formatar_numero(total_insercoes))
col3.metric("Total de Clientes", formatar_numero(total_clientes))
col4.metric("Cliente Destaque", cliente_mais_frequente)

# --- Análises Visuais com Plotly ---
st.subheader("Gráficos")

col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_agregado.empty:
        top_clientes = df_agregado.nlargest(15, 'Inserções').sort_values(by='Inserções', ascending=True)
        grafico_clientes = px.bar(
            top_clientes, x='Inserções', y='Cliente', orientation='h',
            title="Top 15 Clientes por Nº de Inserções",
            labels={'Inserções': 'Quantidade de Inserções', 'Cliente': ''},
            text='Inserções'
        )
        grafico_clientes.update_layout(title_x=0.1, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(grafico_clientes, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de clientes.")

with col_graf2:
    if not df_agregado.empty and df_agregado['Inserções'].sum() > 0:
        grafico_dist = px.pie(
            df_agregado.nlargest(10, 'Inserções'), names='Cliente', values='Inserções',
            title='Proporção de Inserções (Top 10 Clientes)', hole=0.4
        )
        grafico_dist.update_traces(textinfo='percent+label', textposition='inside')
        grafico_dist.update_layout(showlegend=False, title_x=0.15)
        st.plotly_chart(grafico_dist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de proporção.")

# --- Tabela de Dados Detalhados com Novas Colunas ---
st.markdown("---")
st.subheader(f"Dados Detalhados de Contratos (Movimentação de Agosto de 2025)")

# Define a ordem e quais colunas serão exibidas
colunas_para_exibir = [
    'Cliente',
    'Entrou?',
    'Data de Entrada',
    'Saiu?',
    'Data de Saída',
    'Data_Inicio',
    'Data_Fim',
    'Inserções',
    'Código',
    'Agência'
]

# Renomeia as colunas para melhor visualização na tabela
df_para_exibir = df_filtrado[colunas_para_exibir].rename(columns={
    'Data_Inicio': 'Início do Contrato',
    'Data_Fim': 'Fim do Contrato'
})

st.dataframe(
    df_para_exibir,
    # Formatação para as colunas de data
    column_config={
        "Data de Entrada": st.column_config.DateColumn("Data de Entrada", format="DD/MM/YYYY"),
        "Data de Saída": st.column_config.DateColumn("Data de Saída", format="DD/MM/YYYY"),
        "Início do Contrato": st.column_config.DateColumn("Início do Contrato", format="DD/MM/YYYY"),
        "Fim do Contrato": st.column_config.DateColumn("Fim do Contrato", format="DD/MM/YYYY"),
    },
    hide_index=True,
    use_container_width=True
)



