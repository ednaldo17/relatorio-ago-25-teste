import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import locale # Importado para formatar o nome do mês

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
        # Tenta carregar o CSV. Se o seu separador for ponto e vírgula, use: pd.read_csv("relatorio MAI.csv", sep=";")
        df = pd.read_csv("relatorio MAI.csv")

        # --- AJUDA PARA DEBUG ---
        st.info("Nomes das colunas encontradas no arquivo CSV (copie e cole os nomes corretos abaixo):")
        st.write(df.columns.tolist())

        # --- MAPEAMENTO DE COLUNAS ---
        # AJUSTE AQUI: Substitua os nomes à direita pelos nomes exatos do seu arquivo CSV.
        mapa_colunas = {
            "inicio_contrato": "Data_Início", # Ex: "Data Início" ou "Início"
            "fim_contrato": "Data_Fim",       # Ex: "Data Final" ou "Fim"
            "cliente": "Cliente",
            "agencia": "Agência",
            "insercoes": "Inserções",
            "codigo": "Código"
        }

        # Renomeia as colunas do DataFrame para um padrão que o script espera
        df = df.rename(columns={
            mapa_colunas["inicio_contrato"]: "Data_Inicio_Padrao",
            mapa_colunas["fim_contrato"]: "Data_Fim_Padrao",
            mapa_colunas["cliente"]: "Cliente_Padrao",
            mapa_colunas["agencia"]: "Agencia_Padrao",
            mapa_colunas["insercoes"]: "Insercoes_Padrao",
            mapa_colunas["codigo"]: "Codigo_Padrao"
        })

        # Converte colunas de data
        df['Data_Inicio_Padrao'] = pd.to_datetime(df['Data_Inicio_Padrao'], errors='coerce')
        df['Data_Fim_Padrao'] = pd.to_datetime(df['Data_Fim_Padrao'], errors='coerce')

        # --- LÓGICA PARA AS NOVAS COLUNAS ---
        data_atual = datetime.now()
        mes_atual = data_atual.month
        ano_atual = data_atual.year

        condicao_entrou = (df['Data_Inicio_Padrao'].dt.month == mes_atual) & (df['Data_Inicio_Padrao'].dt.year == ano_atual)
        df['Entrou?'] = np.where(condicao_entrou, 'Sim', 'Não')

        condicao_saiu = (df['Data_Fim_Padrao'].dt.month == mes_atual) & (df['Data_Fim_Padrao'].dt.year == ano_atual)
        df['Saiu?'] = np.where(condicao_saiu, 'Sim', 'Não')

        df['Data de Entrada'] = np.where(df['Entrou?'] == 'Sim', df['Data_Inicio_Padrao'], pd.NaT)
        df['Data de Saída'] = np.where(df['Saiu?'] == 'Sim', df['Data_Fim_Padrao'], pd.NaT)

        return df
    except FileNotFoundError:
        st.error("Erro: O arquivo 'relatorio MAI.csv' não foi encontrado. Certifique-se de que ele está na mesma pasta que o script.")
        return None
    except KeyError as e:
        st.error(f"Erro de Chave (KeyError): A coluna {e} não foi encontrada no arquivo CSV. "
                 f"Verifique se o nome da coluna está correto na seção 'MAPEAMENTO DE COLUNAS' do código.")
        return None


df = carregar_dados()

if df is None:
    st.stop()

# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros")

clientes_disponiveis = sorted(df['Cliente_Padrao'].unique())
clientes_selecionados = st.sidebar.multiselect("Cliente", clientes_disponiveis, default=clientes_disponiveis)

agencias_disponiveis = sorted(df['Agencia_Padrao'].dropna().unique())
agencias_selecionadas = st.sidebar.multiselect("Agência", agencias_disponiveis, default=agencias_disponiveis)

# --- Filtragem do DataFrame ---
df_filtrado = df.copy()
if not clientes_selecionados:
    df_filtrado = pd.DataFrame(columns=df.columns)
else:
    df_filtrado = df[
        (df['Cliente_Padrao'].isin(clientes_selecionados)) &
        (df['Agencia_Padrao'].isin(agencias_selecionadas) | df['Agencia_Padrao'].isna())
    ]

# Agrega os dados para as métricas e gráficos
df_agregado = df_filtrado.groupby('Cliente_Padrao').agg(
    Inserções=('Insercoes_Padrao', 'sum')
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
    total_clientes = df_agregado['Cliente_Padrao'].nunique()
    cliente_mais_frequente = df_agregado.loc[df_agregado['Inserções'].idxmax()]['Cliente_Padrao']
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
            top_clientes, x='Inserções', y='Cliente_Padrao', orientation='h',
            title="Top 15 Clientes por Nº de Inserções",
            labels={'Inserções': 'Quantidade de Inserções', 'Cliente_Padrao': ''},
            text='Inserções'
        )
        grafico_clientes.update_layout(title_x=0.1, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(grafico_clientes, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de clientes.")

with col_graf2:
    if not df_agregado.empty and df_agregado['Inserções'].sum() > 0:
        grafico_dist = px.pie(
            df_agregado.nlargest(10, 'Inserções'), names='Cliente_Padrao', values='Inserções',
            title='Proporção de Inserções (Top 10 Clientes)', hole=0.4
        )
        grafico_dist.update_traces(textinfo='percent+label', textposition='inside')
        grafico_dist.update_layout(showlegend=False, title_x=0.15)
        st.plotly_chart(grafico_dist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de proporção.")

# --- Tabela de Dados Detalhados com Novas Colunas ---
st.markdown("---")

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

data_atual = datetime.now()
nome_mes_atual = data_atual.strftime('%B').capitalize()
ano_atual = data_atual.year
st.subheader(f"Dados Detalhados de Contratos (Movimentação de {nome_mes_atual} de {ano_atual})")

colunas_para_exibir = [
    'Cliente_Padrao',
    'Entrou?',
    'Data de Entrada',
    'Saiu?',
    'Data de Saída',
    'Data_Inicio_Padrao',
    'Data_Fim_Padrao',
    'Insercoes_Padrao',
    'Codigo_Padrao',
    'Agencia_Padrao'
]

df_para_exibir = df_filtrado[colunas_para_exibir].rename(columns={
    'Cliente_Padrao': 'Cliente',
    'Data_Inicio_Padrao': 'Início do Contrato',
    'Data_Fim_Padrao': 'Fim do Contrato',
    'Insercoes_Padrao': 'Inserções',
    'Codigo_Padrao': 'Código',
    'Agencia_Padrao': 'Agência'
})

st.dataframe(
    df_para_exibir,
    column_config={
        "Data de Entrada": st.column_config.DateColumn("Data de Entrada", format="DD/MM/YYYY"),
        "Data de Saída": st.column_config.DateColumn("Data de Saída", format="DD/MM/YYYY"),
        "Início do Contrato": st.column_config.DateColumn("Início do Contrato", format="DD/MM/YYYY"),
        "Fim do Contrato": st.column_config.DateColumn("Fim do Contrato", format="DD/MM/YYYY"),
    },
    hide_index=True,
    use_container_width=True
)

