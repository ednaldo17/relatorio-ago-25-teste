import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Inserções de Rádio",
    page_icon="📻",
    layout="wide",
)

# --- Função para obter o nome do mês em português ---
def obter_nome_mes_pt(data):
    """Retorna o nome do mês de uma data em português."""
    meses_pt = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    return meses_pt[data.month - 1]

# --- Carregamento e Preparação dos Dados ---
@st.cache_data
def carregar_dados():
    try:
        # Tenta carregar o CSV. Se o seu separador for ponto e vírgula, use: pd.read_csv("relatorio MAI.csv", sep=";")
        df = pd.read_csv("relatorio MAI.csv")

        # --- AJUDA PARA DEBUG ---
        st.info("Nomes das colunas encontradas no arquivo CSV (use para corrigir o mapa abaixo):")
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

        # --- VALIDAÇÃO DO MAPEAMENTO ---
        colunas_necessarias = list(mapa_colunas.values())
        colunas_faltando = [col for col in colunas_necessarias if col not in df.columns]

        if colunas_faltando:
            st.error(
                f"Erro de Mapeamento: As seguintes colunas não foram encontradas no arquivo CSV: **{', '.join(colunas_faltando)}**. "
                f"Por favor, corrija os nomes na seção 'MAPEAMENTO DE COLUNAS' para que correspondam exatamente aos nomes listados acima."
            )
            return None

        mapa_rename_inverso = {v: k for k, v in mapa_colunas.items()}
        df = df.rename(columns=mapa_rename_inverso)

        df['inicio_contrato'] = pd.to_datetime(df['inicio_contrato'], errors='coerce')
        df['fim_contrato'] = pd.to_datetime(df['fim_contrato'], errors='coerce')

        # --- LÓGICA PARA AS NOVAS COLUNAS ---
        data_atual = datetime.now()
        mes_atual = data_atual.month
        ano_atual = data_atual.year

        condicao_entrou = (df['inicio_contrato'].dt.month == mes_atual) & (df['inicio_contrato'].dt.year == ano_atual)
        df['Entrou?'] = np.where(condicao_entrou, 'Sim', 'Não')

        condicao_saiu = (df['fim_contrato'].dt.month == mes_atual) & (df['fim_contrato'].dt.year == ano_atual)
        df['Saiu?'] = np.where(condicao_saiu, 'Sim', 'Não')

        df['Data de Entrada'] = np.where(df['Entrou?'] == 'Sim', df['inicio_contrato'], pd.NaT)
        df['Data de Saída'] = np.where(df['Saiu?'] == 'Sim', df['fim_contrato'], pd.NaT)

        return df
    except FileNotFoundError:
        st.error("Erro: O arquivo 'relatorio MAI.csv' não foi encontrado. Certifique-se de que ele está na mesma pasta que o script.")
        return None

df = carregar_dados()

if df is None:
    st.stop()

# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros")

clientes_disponiveis = sorted(df['cliente'].unique())
clientes_selecionados = st.sidebar.multiselect("Cliente", clientes_disponiveis, default=clientes_disponiveis)

agencias_disponiveis = sorted(df['agencia'].dropna().unique())
agencias_selecionadas = st.sidebar.multiselect("Agência", agencias_disponiveis, default=agencias_disponiveis)

# --- Filtragem do DataFrame ---
df_filtrado = df.copy()
if not clientes_selecionados:
    df_filtrado = pd.DataFrame(columns=df.columns)
else:
    df_filtrado = df[
        (df['cliente'].isin(clientes_selecionados)) &
        (df['agencia'].isin(agencias_selecionadas) | df['agencia'].isna())
    ]

df_agregado = df_filtrado.groupby('cliente').agg(
    Inserções=('insercoes', 'sum')
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
    total_clientes = df_agregado['cliente'].nunique()
    cliente_mais_frequente = df_agregado.loc[df_agregado['Inserções'].idxmax()]['cliente']
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
            top_clientes, x='Inserções', y='cliente', orientation='h',
            title="Top 15 Clientes por Nº de Inserções",
            labels={'Inserções': 'Quantidade de Inserções', 'cliente': ''},
            text='Inserções'
        )
        grafico_clientes.update_layout(title_x=0.1, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(grafico_clientes, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de clientes.")

with col_graf2:
    if not df_agregado.empty and df_agregado['Inserções'].sum() > 0:
        grafico_dist = px.pie(
            df_agregado.nlargest(10, 'Inserções'), names='cliente', values='Inserções',
            title='Proporção de Inserções (Top 10 Clientes)', hole=0.4
        )
        grafico_dist.update_traces(textinfo='percent+label', textposition='inside')
        grafico_dist.update_layout(showlegend=False, title_x=0.15)
        st.plotly_chart(grafico_dist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de proporção.")

# --- Tabela de Dados Detalhados com Novas Colunas ---
st.markdown("---")

# Usa a nova função para obter o título dinâmico
data_atual = datetime.now()
nome_mes_atual = obter_nome_mes_pt(data_atual)
ano_atual = data_atual.year
st.subheader(f"Dados Detalhados de Contratos (Movimentação de {nome_mes_atual} de {ano_atual})")

colunas_para_exibir = [
    'cliente',
    'Entrou?',
    'Data de Entrada',
    'Saiu?',
    'Data de Saída',
    'inicio_contrato',
    'fim_contrato',
    'insercoes',
    'codigo',
    'agencia'
]

df_para_exibir = df_filtrado[colunas_para_exibir].rename(columns={
    'cliente': 'Cliente',
    'inicio_contrato': 'Início do Contrato',
    'fim_contrato': 'Fim do Contrato',
    'insercoes': 'Inserções',
    'codigo': 'Código',
    'agencia': 'Agência'
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
