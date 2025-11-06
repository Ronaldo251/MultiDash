# app.py
from flask import Flask, render_template, jsonify, request
import pandas as pd
import geopandas as gpd
import os

# --------------------------------------------------------------------------
# 1. INICIALIZAÇÃO DA APLICAÇÃO FLASK
# --------------------------------------------------------------------------
app = Flask(__name__)

# --------------------------------------------------------------------------
# 2. CARREGAMENTO E PRÉ-PROCESSAMENTO GLOBAL DOS DADOS
#    (Isso é executado apenas uma vez quando o servidor inicia)
# --------------------------------------------------------------------------
def carregar_e_preparar_dados():
    """Carrega todos os datasets necessários e faz o pré-processamento inicial."""
    try:
        # Carrega os arquivos
        df_crimes = pd.read_csv('crimes.csv', sep=',')
        gdf_municipios = gpd.read_file('municipios_ce.geojson')
        df_populacao = pd.read_csv('populacao_ce.csv')
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: Arquivo '{e.filename}' não encontrado. A aplicação não pode iniciar.")
        # Em um ambiente de produção, você poderia usar sys.exit() aqui
        return None, None, None

    # Padroniza os nomes das colunas
    df_crimes.columns = [
        'AIS', 'NATUREZA', 'MUNICIPIO', 'LOCAL', 'DATA', 'HORA', 'DIA_SEMANA',
        'MEIO_EMPREGADO', 'GENERO', 'ORIENTACAO_SEXUAL', 'IDADE_VITIMA',
        'ESCOLARIDADE_VITIMA', 'RACA_VITIMA'
    ]

    # Converte colunas de data e cria 'ANO'
    df_crimes['DATA'] = pd.to_datetime(df_crimes['DATA'], dayfirst=True, errors='coerce')
    df_crimes.dropna(subset=['DATA'], inplace=True)
    df_crimes['ANO'] = df_crimes['DATA'].dt.year

    # Agrupamento de gênero
    mapeamento_genero = {
        'Masculino': 'Masculino', 'Homem Trans': 'Masculino',
        'Feminino': 'Feminino', 'Mulher Trans': 'Feminino', 'Travesti': 'Feminino'
    }
    df_crimes['GENERO_AGRUPADO'] = df_crimes['GENERO'].map(mapeamento_genero)

    # Normaliza nomes de municípios para facilitar os merges
    def normalize_text(text_series):
        return text_series.str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    df_crimes['MUNICIPIO_NORM'] = normalize_text(df_crimes['MUNICIPIO'])
    gdf_municipios['NM_MUN_NORM'] = normalize_text(gdf_municipios['name'])
    df_populacao['MUNICIPIO_NORM'] = normalize_text(df_populacao['municipio'])
    
    print("Dados carregados e pré-processados com sucesso.")
    return df_crimes, gdf_municipios, df_populacao

# Executa o carregamento
df_crimes_global, gdf_municipios_global, df_populacao_global = carregar_e_preparar_dados()

# --------------------------------------------------------------------------
# 3. DEFINIÇÃO DAS ROTAS (ENDPOINTS) DA APLICAÇÃO
# --------------------------------------------------------------------------

@app.route('/')
def index():
    """
    Rota principal que renderiza o arquivo 'index.html'.
    Também passa a lista de crimes para popular o seletor na sidebar.
    """
    # Gera a lista de naturezas de crime para o filtro
    lista_crimes = sorted(df_crimes_global['NATUREZA'].dropna().unique().tolist())
    return render_template('index.html', crimes=lista_crimes)

@app.route('/api/dados_mapa')
def get_map_data():
    """
    Endpoint de API. O frontend (JavaScript) fará uma requisição para esta URL
    para obter os dados geográficos já processados com as taxas de criminalidade.
    """
    # Pega o tipo de crime selecionado como um parâmetro da URL
    # Ex: /api/dados_mapa?crime=HOMICIDIO%20DOLOSO
    crime_selecionado = request.args.get('crime', 'HOMICIDIO DOLOSO') # Valor padrão

    # Filtra os crimes pela natureza selecionada
    df_filtrado = df_crimes_global[df_crimes_global['NATUREZA'] == crime_selecionado]
    
    # Agrega os crimes por município
    crimes_por_municipio = df_filtrado.groupby('MUNICIPIO_NORM').size().reset_index(name='QUANTIDADE')

    # Junta com os dados de população
    dados_completos = pd.merge(
        gdf_municipios_global,
        df_populacao_global[['MUNICIPIO_NORM', 'populacao']],
        left_on='NM_MUN_NORM',
        right_on='MUNICIPIO_NORM',
        how='left'
    )
    
    # Junta o resultado com a contagem de crimes
    mapa_data = pd.merge(
        dados_completos,
        crimes_por_municipio,
        on='MUNICIPIO_NORM',
        how='left'
    )

    # Preenche valores nulos e calcula a taxa
    mapa_data['QUANTIDADE'] = mapa_data['QUANTIDADE'].fillna(0).astype(int)
    mapa_data['populacao'] = mapa_data['populacao'].fillna(1).astype(int) # Evita divisão por zero
    mapa_data['TAXA_POR_100K'] = (mapa_data['QUANTIDADE'] / mapa_data['populacao']) * 100000
    mapa_data['TAXA_POR_100K'] = mapa_data['TAXA_POR_100K'].fillna(0)

    # Converte o GeoDataFrame para um formato JSON que o Leaflet.js entende
    # O método to_json() do GeoPandas já cria um GeoJSON válido
    return jsonify(mapa_data.to_json())

# Rota para fornecer a lista de municípios para a caixa de busca
@app.route('/api/municipios')
def get_municipios():
    lista_municipios = sorted(gdf_municipios_global['name'].unique().tolist())
    return jsonify(lista_municipios)

# Adicione aqui as rotas de API para os gráficos conforme necessário
# Exemplo:
# @app.route('/api/grafico1')
# def get_data_grafico1():
#     # Lógica para preparar os dados do Gráfico 1
#     # ...
#     # return jsonify(dados_do_grafico)


# --------------------------------------------------------------------------
# 4. EXECUÇÃO DO SERVIDOR
# --------------------------------------------------------------------------
if __name__ == '__main__':
    # 'debug=True' faz com que o servidor reinicie automaticamente após cada alteração no código.
    # Desative isso em um ambiente de produção.
    app.run(debug=True)

