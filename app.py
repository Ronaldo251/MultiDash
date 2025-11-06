# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(layout="wide", page_title="Análise Criminal - Ceará")
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 9)
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 14

# ==============================================================================
# CARREGAMENTO E CACHE DOS DADOS
# ==============================================================================
@st.cache_data
def carregar_dados():
    """Carrega e prepara os dados uma única vez."""
    try:
        df_crimes = pd.read_csv('crimes.csv', sep=',')
        gdf_municipios = gpd.read_file('municipios_ce.geojson')
        df_populacao = pd.read_csv('populacao_ce.csv')
    except FileNotFoundError as e:
        st.error(f"Erro: Arquivo não encontrado. Verifique se '{e.filename}' está na pasta do projeto.")
        st.stop()

    df_crimes.columns = [
        'AIS', 'NATUREZA', 'MUNICIPIO', 'LOCAL', 'DATA', 'HORA', 'DIA_SEMANA',
        'MEIO_EMPREGADO', 'GENERO', 'ORIENTACAO_SEXUAL', 'IDADE_VITIMA',
        'ESCOLARIDADE_VITIMA', 'RACA_VITIMA'
    ]
    
    df_crimes['DATA'] = pd.to_datetime(df_crimes['DATA'], dayfirst=True, errors='coerce')
    df_crimes.dropna(subset=['DATA'], inplace=True)
    df_crimes['ANO'] = df_crimes['DATA'].dt.year
    
    mapeamento_genero = {'Masculino': 'Masculino', 'Homem Trans': 'Masculino', 'Feminino': 'Feminino', 'Mulher Trans': 'Feminino', 'Travesti': 'Feminino'}
    df_crimes['GENERO_AGRUPADO'] = df_crimes['GENERO'].map(mapeamento_genero)
    
    return df_crimes, gdf_municipios, df_populacao

df_crimes_original, gdf_municipios, df_populacao = carregar_dados()

@st.cache_data
def preparar_dados_mapa(_df_crimes, _gdf_municipios, _df_populacao, tipo_crime_geo):
    """Pré-calcula os dados para o mapa, aplicando cache por tipo de crime."""
    def normalize_text(text_series):
        return text_series.str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    df_crimes_copy = _df_crimes.copy()
    gdf_municipios_copy = _gdf_municipios.copy()
    df_populacao_copy = _df_populacao.copy()

    df_crimes_copy['MUNICIPIO_NORM'] = normalize_text(df_crimes_copy['MUNICIPIO'])
    gdf_municipios_copy['NM_MUN_NORM'] = normalize_text(gdf_municipios_copy['name'])
    df_populacao_copy['MUNICIPIO_NORM'] = normalize_text(df_populacao_copy['municipio'])

    df_filtrado = df_crimes_copy[df_crimes_copy['NATUREZA'] == tipo_crime_geo]
    crimes_por_municipio = df_filtrado.groupby('MUNICIPIO_NORM').size().reset_index(name='QUANTIDADE')
    
    dados_completos = pd.merge(
        crimes_por_municipio,
        df_populacao_copy[['MUNICIPIO_NORM', 'populacao']],
        on='MUNICIPIO_NORM',
        how='left'
    )
    dados_completos.dropna(subset=['populacao'], inplace=True)
    dados_completos['TAXA_POR_100K'] = (dados_completos['QUANTIDADE'] / dados_completos['populacao']) * 100000
    
    mapa_data = gdf_municipios_copy.merge(
        dados_completos,
        left_on='NM_MUN_NORM',
        right_on='MUNICIPIO_NORM',
        how='left'
    )
    
    mapa_data['QUANTIDADE'] = mapa_data['QUANTIDADE'].fillna(0).astype(int)
    mapa_data['TAXA_POR_100K'] = mapa_data['TAXA_POR_100K'].fillna(0)
    
    return mapa_data

# ==============================================================================
# FUNÇÕES DE GERAÇÃO DE GRÁFICOS
# ==============================================================================
def gerar_grafico_1(df, tipo_analise):
    st.subheader("Gráfico 1: Evolução Anual por Gênero")
    df_analise = df.groupby(['ANO', 'GENERO_AGRUPADO']).size().reset_index(name='TOTAL')
    df_analise.rename(columns={'GENERO_AGRUPADO': 'Gênero'}, inplace=True)
    
    fig, ax = plt.subplots()
    sns.lineplot(data=df_analise, x='ANO', y='TOTAL', hue='Gênero', marker='o', ax=ax)
    ax.set_title(f'Evolução do Número Absoluto de {tipo_analise} no Ceará')
    ax.set_xlabel('Ano')
    ax.set_ylabel(f'Número Total de Ocorrências ({tipo_analise})')
    st.pyplot(fig)

def gerar_grafico_2(df, tipo_analise):
    st.subheader("Gráfico 2: Análise de Crimes por Dia e Hora (Vítimas Femininas)")
    df_feminino = df[df['GENERO_AGRUPADO'] == 'Feminino'].copy()
    if df_feminino.empty:
        st.warning("Não há dados de vítimas femininas para este filtro.")
        return
        
    df_feminino['HORA_NUM'] = pd.to_datetime(df_feminino['HORA'], format='%H:%M:%S', errors='coerce').dt.hour
    df_feminino.dropna(subset=['HORA_NUM'], inplace=True)
    df_feminino['HORA_NUM'] = df_feminino['HORA_NUM'].astype(int)
    ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    df_feminino['DIA_SEMANA'] = pd.Categorical(df_feminino['DIA_SEMANA'], categories=ordem_dias, ordered=True)
    
    crimes_por_dia_hora = df_feminino.groupby(['DIA_SEMANA', 'HORA_NUM']).size().reset_index(name='QUANTIDADE')
    
    fig, ax = plt.subplots()
    sns.lineplot(data=crimes_por_dia_hora, x='HORA_NUM', y='QUANTIDADE', hue='DIA_SEMANA', marker='o', ax=ax)
    ax.set_title(f'{tipo_analise} contra Mulheres por Hora do Dia')
    ax.set_xlabel('Hora do Dia')
    ax.set_ylabel(f'Quantidade de {tipo_analise}')
    ax.set_xticks(range(0, 24))
    ax.legend(title='Dia da Semana')
    st.pyplot(fig)

# ==============================================================================
# FUNÇÃO DE ANÁLISE GEOGRÁFICA
# ==============================================================================
def executar_analise_geografica(mapa_data, tipo_crime_geo, centro_mapa, zoom_mapa, municipio_destacado=None):
    st.header("🗺️ Análise Geográfica de Crimes por Município")
    st.subheader(f"Visualizando Taxa de '{tipo_crime_geo}' por 100 mil Habitantes")

    mapa = folium.Map(location=centro_mapa, zoom_start=zoom_mapa, tiles='CartoDB positron')
    
    choropleth = folium.Choropleth(
        geo_data=mapa_data,
        name='Taxa de Crimes',
        data=mapa_data,
        columns=['NM_MUN_NORM', 'TAXA_POR_100K'],
        key_on='feature.properties.NM_MUN_NORM',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f'Taxa de {tipo_crime_geo} por 100 mil Habitantes',
    ).add_to(mapa)
    
    folium.GeoJson(
        mapa_data,
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'QUANTIDADE', 'TAXA_POR_100K'], 
            aliases=['Município:', 'Nº Absoluto:', 'Taxa/100k Hab:'],
            localize=True,
            style=("background-color: white; color: black; font-family: arial; font-size: 12px; padding: 10px;")
        ),
        style_function=lambda x: {'fillColor': 'transparent', 'color': 'black', 'weight': 0.5}
    ).add_to(choropleth.geojson)

    if municipio_destacado and municipio_destacado != "Estado Completo":
        municipio_geo = mapa_data[mapa_data['name'] == municipio_destacado]
        if not municipio_geo.empty:
            folium.GeoJson(
                municipio_geo,
                style_function=lambda x: {'color': '#0000FF', 'weight': 3, 'fillOpacity': 0.1},
                name=f"Destaque: {municipio_destacado}"
            ).add_to(mapa)

    st_folium(mapa, use_container_width=True, key="mapa_ceara")

# ==============================================================================
# INTERFACE DO USUÁRIO (SIDEBAR) E LÓGICA PRINCIPAL
# ==============================================================================
st.sidebar.image("https://www.manus.ai/wp-content/uploads/2023/07/logo-manus-blue.png", width=200 )
st.sidebar.title("Análise Criminal - Ceará")

lista_municipios = ["Estado Completo"] + sorted(gdf_municipios['name'].unique().tolist())
municipio_selecionado = st.sidebar.selectbox(
    "🔎 Pesquisar Município",
    options=lista_municipios
)

view_mode = st.sidebar.radio("Escolha a Visualização Principal:", ["Gráficos", "Mapa"], index=1)
st.sidebar.markdown("---")

if view_mode == "Gráficos":
    with st.sidebar.expander("📊 Opções de Gráficos", expanded=True):
        analise_graficos = st.radio(
            "Selecione o Foco da Análise:",
            ("Análise Geral de Crimes", "Análise de Crimes Contra Mulheres"),
            key="analise_graficos_radio"
        )
        
        escopo_crime = st.radio(
            "Selecione o Escopo dos Crimes:",
            ("Todos os Tipos", "Apenas Homicídios"),
            key="escopo_crime_radio"
        )

        opcoes_graficos = ["Gráfico 1: Evolução Anual por Gênero"]
        if analise_graficos == "Crimes Contra Mulheres":
            opcoes_graficos.append("Gráfico 2: Crimes por Dia e Hora")
        
        grafico_selecionado = st.selectbox("Escolha o Gráfico:", opcoes_graficos)

    if analise_graficos == "Análise Geral de Crimes":
        df_filtrado_grafico = df_crimes_original.copy()
        titulo_contexto = "Todos os Crimes"
    else:
        df_filtrado_grafico = df_crimes_original[df_crimes_original['GENERO_AGRUPADO'] == 'Feminino'].copy()
        titulo_contexto = "Crimes Contra Mulheres"

    if escopo_crime == "Apenas Homicídios":
        naturezas_homicidio = ['HOMICIDIO DOLOSO', 'FEMINICIDIO', 'LATROCINIO', 'LESAO CORPORAL SEGUIDA DE MORTE']
        df_filtrado_grafico = df_filtrado_grafico[df_filtrado_grafico['NATUREZA'].isin(naturezas_homicidio)]
        titulo_contexto += " (Foco em Homicídios)"

    st.header(f"Análise de Gráficos: {analise_graficos}")
    st.markdown(f"**Contexto:** {titulo_contexto}")

    if grafico_selecionado == "Gráfico 1: Evolução Anual por Gênero":
        gerar_grafico_1(df_filtrado_grafico, titulo_contexto)
    elif grafico_selecionado == "Gráfico 2: Crimes por Dia e Hora":
        gerar_grafico_2(df_filtrado_grafico, titulo_contexto)

else: # view_mode == "Mapa"
    with st.sidebar.expander("🗺️ Opções do Mapa", expanded=True):
        lista_crimes = sorted(df_crimes_original['NATUREZA'].dropna().unique().tolist())
        crime_geo_selecionado = st.selectbox(
            "Selecione o Tipo de Crime:",
            lista_crimes,
            index=lista_crimes.index('HOMICIDIO DOLOSO')
        )

    if municipio_selecionado == "Estado Completo":
        centro_mapa = [-5.0, -39.5]
        zoom_mapa = 7
    else:
        municipio_geo = gdf_municipios[gdf_municipios['name'] == municipio_selecionado]
        if not municipio_geo.empty:
            centroide = municipio_geo.geometry.centroid.iloc[0]
            centro_mapa = [centroide.y, centroide.x]
            zoom_mapa = 10
        else:
            centro_mapa = [-5.0, -39.5]
            zoom_mapa = 7
    
    mapa_data = preparar_dados_mapa(df_crimes_original, gdf_municipios, df_populacao, crime_geo_selecionado)
    
    executar_analise_geografica(mapa_data, crime_geo_selecionado, centro_mapa, zoom_mapa, municipio_selecionado)
