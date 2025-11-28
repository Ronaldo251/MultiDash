import os
import pandas as pd
import geopandas as gpd
from flask import Flask, jsonify, render_template, request
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
import warnings

from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning) 
pd.options.mode.chained_assignment = None 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.json.ensure_ascii = False

print("Iniciando o carregamento e processamento dos dados...")
try:
    crimes_path = os.path.join(BASE_DIR, 'crimes.csv')
    municipios_path = os.path.join(BASE_DIR, 'municipios_ce.geojson')
    populacao_path = os.path.join(BASE_DIR, 'populacao_ce.csv')

    df_crimes_raw = pd.read_csv(crimes_path, sep=',')
    gdf_municipios_raw = gpd.read_file(municipios_path)
    df_populacao = pd.read_csv(populacao_path)
    
    df_crimes_raw.columns = [
        'AIS', 'NATUREZA', 'MUNICIPIO', 'LOCAL', 'DATA', 'HORA', 'DIA_SEMANA',
        'MEIO_EMPREGADO', 'GENERO', 'ORIENTACAO_SEXUAL', 'IDADE_VITIMA',
        'ESCOLARIDADE_VITIMA', 'RACA_VITIMA'
    ]
except FileNotFoundError as e:
    print(f"ERRO CRÍTICO: Arquivo não encontrado - {e}.")
    exit()
except Exception as e:
    print(f"ERRO ao ler os arquivos CSV. Verifique o separador (deve ser vírgula) e o número de colunas. Erro: {e}")
    exit()

df_crimes_raw['DATA'] = pd.to_datetime(df_crimes_raw['DATA'], dayfirst=True, errors='coerce')
df_crimes_raw.dropna(subset=['DATA'], inplace=True)
df_crimes_graficos = df_crimes_raw.copy()
df_crimes_graficos['ANO'] = df_crimes_graficos['DATA'].dt.year
df_crimes_graficos['MES'] = df_crimes_graficos['DATA'].dt.month
mapeamento_genero = {'MASCULINO': 'Masculino', 'HOMEM TRANS': 'Masculino', 'FEMININO': 'Feminino', 'MULHER TRANS': 'Feminino', 'TRAVESTI': 'Feminino'}
df_crimes_graficos['GENERO_AGRUPADO'] = df_crimes_graficos['GENERO'].str.upper().str.strip().map(mapeamento_genero)

def get_clean_age_df(df_base):
    """Função auxiliar para limpar e preparar dados de idade."""
    df_idade = df_base.copy()
    df_idade['IDADE_NUM'] = pd.to_numeric(df_idade['IDADE_VITIMA'], errors='coerce')
    df_idade.dropna(subset=['IDADE_NUM'], inplace=True)
    df_idade['IDADE_NUM'] = df_idade['IDADE_NUM'].astype(int)
    df_idade = df_idade[(df_idade['IDADE_NUM'] >= 0) & (df_idade['IDADE_NUM'] <= 110)]
    return df_idade

def apply_filters(df, filters): # Deve receber 'df' como primeiro argumento
    """Aplica uma série de filtros de um objeto JSON a um DataFrame."""
    df_filtered = df.copy()

    # Filtro de Data
    start_date = filters['dates'].get('start')
    end_date = filters['dates'].get('end')
    if start_date and 'DATA' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['DATA'] >= pd.to_datetime(start_date)]
    if end_date and 'DATA' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['DATA'] <= pd.to_datetime(end_date)]

    # Filtros de Checkbox
    for column, values in filters['checkboxes'].items():
        if values and column in df_filtered.columns:
            cleaned_values = [str(v).strip() for v in values]
            df_filtered = df_filtered[df_filtered[column].astype(str).str.strip().isin(cleaned_values)]
    
    return df_filtered

def normalize_text(text_series):
    return text_series.str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

crimes_agrupados_mun = df_crimes_raw.groupby(['MUNICIPIO', 'NATUREZA']).size().reset_index(name='QUANTIDADE')
crimes_agrupados_mun['MUNICIPIO_NORM'] = normalize_text(crimes_agrupados_mun['MUNICIPIO'])
df_populacao['MUNICIPIO_NORM'] = normalize_text(df_populacao['municipio'])
crimes_com_pop_mun = pd.merge(crimes_agrupados_mun, df_populacao[['MUNICIPIO_NORM', 'populacao']], on='MUNICIPIO_NORM', how='left')
crimes_com_pop_mun.dropna(subset=['populacao'], inplace=True)
crimes_com_pop_mun['TAXA_POR_100K'] = (crimes_com_pop_mun['QUANTIDADE'] / crimes_com_pop_mun['populacao']) * 100000

gdf_municipios_raw['NM_MUN_NORM'] = normalize_text(gdf_municipios_raw['name'])

municipios_com_centroide = gdf_municipios_raw.copy()
municipios_com_centroide_proj = municipios_com_centroide.to_crs('epsg:31984')
centroides_proj = municipios_com_centroide_proj['geometry'].centroid
municipios_com_centroide['centroid'] = centroides_proj.to_crs(gdf_municipios_raw.crs)

municipios_ais_map = {'Fortaleza': 'AIS 1-10', 'Caucaia': 'AIS 11', 'Maracanaú': 'AIS 12', 'Aquiraz': 'AIS 13', 'Cascavel': 'AIS 13', 'Eusébio': 'AIS 13', 'Pindoretama': 'AIS 13', 'Alcântaras': 'AIS 14', 'Barroquinha': 'AIS 14', 'Camocim': 'AIS 14', 'Cariré': 'AIS 14', 'Carnaubal': 'AIS 14', 'Chaval': 'AIS 14', 'Coreaú': 'AIS 14', 'Croatá': 'AIS 14', 'Forquilha': 'AIS 14', 'Frecheirinha': 'AIS 14', 'Graça': 'AIS 14', 'Granja': 'AIS 14', 'Groaíras': 'AIS 14', 'Guaraciaba do Norte': 'AIS 14', 'Ibiapina': 'AIS 14', 'Martinópole': 'AIS 14', 'Massapê': 'AIS 14', 'Meruoca': 'AIS 14', 'Moraújo': 'AIS 14', 'Mucambo': 'AIS 14', 'Pacujá': 'AIS 14', 'Santana do Acaraú': 'AIS 14', 'São Benedito': 'AIS 14', 'Senador Sá': 'AIS 14', 'Sobral': 'AIS 14', 'Tianguá': 'AIS 14', 'Ubajara': 'AIS 14', 'Uruoca': 'AIS 14', 'Viçosa do Ceará': 'AIS 14', 'Acarape': 'AIS 15', 'Aracoiaba': 'AIS 15', 'Aratuba': 'AIS 15', 'Barreira': 'AIS 15', 'Baturité': 'AIS 15', 'Boa Viagem': 'AIS 15', 'Canindé': 'AIS 15', 'Capistrano': 'AIS 15', 'Caridade': 'AIS 15', 'Guaramiranga': 'AIS 15', 'Itapiúna': 'AIS 15', 'Itatira': 'AIS 15', 'Madalena': 'AIS 15', 'Mulungu': 'AIS 15', 'Ocara': 'AIS 15', 'Pacoti': 'AIS 15', 'Palmácia': 'AIS 15', 'Paramoti': 'AIS 15', 'Redenção': 'AIS 15', 'Ararendá': 'AIS 16', 'Catunda': 'AIS 16', 'Crateús': 'AIS 16', 'Hidrolândia': 'AIS 16', 'Independência': 'AIS 16', 'Ipaporanga': 'AIS 16', 'Ipu': 'AIS 16', 'Ipueiras': 'AIS 16', 'Monsenhor Tabosa': 'AIS 16', 'Nova Russas': 'AIS 16', 'Novo Oriente': 'AIS 16', 'Pires Ferreira': 'AIS 16', 'Poranga': 'AIS 16', 'Reriutaba': 'AIS 16', 'Santa Quitéria': 'AIS 16', 'Tamboril': 'AIS 16', 'Varjota': 'AIS 16', 'Acaraú': 'AIS 17', 'Amontada': 'AIS 17', 'Apuiarés': 'AIS 17', 'Bela Cruz': 'AIS 17', 'Cruz': 'AIS 17', 'General Sampaio': 'AIS 17', 'Irauçuba': 'AIS 17', 'Itapajé': 'AIS 17', 'Itapipoca': 'AIS 17', 'Itarema': 'AIS 17', 'Jijoca de Jericoacoara': 'AIS 17', 'Marco': 'AIS 17', 'Miraíma': 'AIS 17', 'Morrinhos': 'AIS 17', 'Pentecoste': 'AIS 17', 'Tejuçuoca': 'AIS 17', 'Tururu': 'AIS 17', 'Umirim': 'AIS 17', 'Uruburetama': 'AIS 17', 'Alto Santo': 'AIS 18', 'Aracati': 'AIS 18', 'Beberibe': 'AIS 18', 'Ererê': 'AIS 18', 'Fortim': 'AIS 18', 'Icapuí': 'AIS 18', 'Iracema': 'AIS 18', 'Itaiçaba': 'AIS 18', 'Jaguaribe': 'AIS 18', 'Jaguaruana': 'AIS 18', 'Limoeiro do Norte': 'AIS 18', 'Jaguaribara': 'AIS 18', 'Palhano': 'AIS 18', 'Pereiro': 'AIS 18', 'Potiretama': 'AIS 18', 'Quixeré': 'AIS 18', 'Russas': 'AIS 18', 'São João do Jaguaribe': 'AIS 18', 'Tabuleiro do Norte': 'AIS 18', 'Abaiara': 'AIS 19', 'Altaneira': 'AIS 19', 'Antonina do Norte': 'AIS 19', 'Araripe': 'AIS 19', 'Assaré': 'AIS 19', 'Aurora': 'AIS 19', 'Barbalha': 'AIS 19', 'Barro': 'AIS 19', 'Brejo Santo': 'AIS 19', 'Campos Sales': 'AIS 19', 'Caririaçu': 'AIS 19', 'Crato': 'AIS 19', 'Farias Brito': 'AIS 19', 'Jardim': 'AIS 19', 'Jati': 'AIS 19', 'Juazeiro do Norte': 'AIS 19', 'Mauriti': 'AIS 19', 'Milagres': 'AIS 19', 'Missão Velha': 'AIS 19', 'Nova Olinda': 'AIS 19', 'Penaforte': 'AIS 19', 'Porteiras': 'AIS 19', 'Potengi': 'AIS 19', 'Salitre': 'AIS 19', 'Santana do Cariri': 'AIS 19', 'Banabuiú': 'AIS 20', 'Choró': 'AIS 20', 'Deputado Irapuan Pinheiro': 'AIS 20', 'Ibaretama': 'AIS 20', 'Ibicuitinga': 'AIS 20', 'Jaguaretama': 'AIS 20', 'Milhã': 'AIS 20', 'Morada Nova': 'AIS 20', 'Pedra Branca': 'AIS 20', 'Quixadá': 'AIS 20', 'Quixeramobim': 'AIS 20', 'Senador Pompeu': 'AIS 20', 'Solonópole': 'AIS 20', 'Acopiara': 'AIS 21', 'Baixio': 'AIS 21', 'Cariús': 'AIS 21', 'Cedro': 'AIS 21', 'Granjeiro': 'AIS 21', 'Icó': 'AIS 21', 'Iguatu': 'AIS 21', 'Ipaumirim': 'AIS 21', 'Jucás': 'AIS 21', 'Lavras da Mangabeira': 'AIS 21', 'Orós': 'AIS 21', 'Quixelô': 'AIS 21', 'Saboeiro': 'AIS 21', 'Tarrafas': 'AIS 21', 'Umari': 'AIS 21', 'Várzea Alegre': 'AIS 21', 'Aiuaba': 'AIS 22', 'Arneiroz': 'AIS 22', 'Catarina': 'AIS 22', 'Mombaça': 'AIS 22', 'Parambu': 'AIS 22', 'Piquet Carneiro': 'AIS 22', 'Quiterianópolis': 'AIS 22', 'Tauá': 'AIS 22', 'Paracuru': 'AIS 23', 'Paraipaba': 'AIS 23', 'São Gonçalo do Amarante': 'AIS 23', 'São Luís do Curu': 'AIS 23', 'Trairi': 'AIS 23', 'Guaiúba': 'AIS 24', 'Maranguape': 'AIS 24', 'Pacatuba': 'AIS 24', 'Chorozinho': 'AIS 25', 'Horizonte': 'AIS 25', 'Itaitinga': 'AIS 25', 'Pacajus': 'AIS 25'}
gdf_municipios_raw['AIS'] = gdf_municipios_raw['name'].map(municipios_ais_map)
gdf_ais = gdf_municipios_raw.dissolve(by='AIS').reset_index()
df_crimes_raw['AIS_MAPEADA'] = df_crimes_raw['MUNICIPIO'].map(municipios_ais_map)
df_populacao['AIS'] = df_populacao['municipio'].map(municipios_ais_map)
pop_por_ais = df_populacao.groupby('AIS')['populacao'].sum().reset_index()
crimes_agrupados_ais = df_crimes_raw.groupby(['AIS_MAPEADA', 'NATUREZA']).size().reset_index(name='QUANTIDADE')
crimes_com_pop_ais = pd.merge(crimes_agrupados_ais, pop_por_ais, left_on='AIS_MAPEADA', right_on='AIS', how='left')
crimes_com_pop_ais.dropna(subset=['populacao'], inplace=True)
crimes_com_pop_ais['TAXA_POR_100K'] = (crimes_com_pop_ais['QUANTIDADE'] / crimes_com_pop_ais['populacao']) * 100000

LISTA_DE_CRIMES = sorted(df_crimes_raw['NATUREZA'].dropna().unique().tolist())

print("Processamento de dados concluído. Aplicação pronta.")
def projetar_ano_incompleto(df_historico, ano_incompleto, ultimo_mes_registrado, colunas_grupo, anos_para_media=5):
    """
    Projeta o total para um ano incompleto com base na média dos meses faltantes 
    dos últimos 'anos_para_media' anos.
    """
    df_ano_incompleto = df_historico[df_historico['ANO'] == ano_incompleto].copy()
    
    ano_inicio_media = ano_incompleto - anos_para_media
    df_anos_anteriores = df_historico[
        (df_historico['ANO'] < ano_incompleto) &
        (df_historico['ANO'] >= ano_inicio_media)
    ].copy()

    if df_anos_anteriores.empty:
        df_anos_anteriores = df_historico[df_historico['ANO'] < ano_incompleto].copy()
        if df_anos_anteriores.empty:
            return df_ano_incompleto.groupby(colunas_grupo + ['ANO'])['TOTAL'].sum().reset_index()

    periodo_faltante = df_anos_anteriores[df_anos_anteriores['MES'] > ultimo_mes_registrado]
    
    soma_periodo_faltante_por_ano = periodo_faltante.groupby(['ANO'] + colunas_grupo)['TOTAL'].sum().reset_index()
    
    media_periodo_faltante = soma_periodo_faltante_por_ano.groupby(colunas_grupo)['TOTAL'].mean().reset_index()
    media_periodo_faltante.rename(columns={'TOTAL': 'ESTIMATIVA_FALTANTE'}, inplace=True)

    total_ano_incompleto = df_ano_incompleto.groupby(colunas_grupo)['TOTAL'].sum().reset_index()

    df_projetado = pd.merge(total_ano_incompleto, media_periodo_faltante, on=colunas_grupo, how='left')
    df_projetado['ESTIMATIVA_FALTANTE'] = df_projetado['ESTIMATIVA_FALTANTE'].fillna(0)
    
    df_projetado['TOTAL'] = df_projetado['TOTAL'] + df_projetado['ESTIMATIVA_FALTANTE']
    
    return df_projetado[colunas_grupo + ['TOTAL']]

@app.route('/')
def index():
    return render_template('index.html', crimes=LISTA_DE_CRIMES)

def get_dataframe(dashboard_id=None):
    if dashboard_id:
        dashboards_dir = os.path.join(BASE_DIR, 'dashboards')
        metadata_path = os.path.join(dashboards_dir, f"{dashboard_id}.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            csv_path = metadata.get("csv_path")
            if csv_path and os.path.exists(csv_path):
                df_custom = pd.read_csv(csv_path)
                
                # --- MUDANÇA CRUCIAL AQUI ---
                # Tenta converter a coluna 'DATA' apenas se ela existir no CSV
                if 'DATA' in df_custom.columns:
                    df_custom['DATA'] = pd.to_datetime(df_custom['DATA'], dayfirst=True, errors='coerce')
                
                return df_custom
    
    # Fallback para o dataframe padrão
    return df_crimes_raw

@app.route('/api/schema')
def get_schema():
    dashboard_id = request.args.get('dashboard_id')
    df = get_dataframe(dashboard_id)
    
    # Define as colunas padrão
    filterable_columns = [
        'NATUREZA', 'MUNICIPIO', 'LOCAL', 'DIA_SEMANA', 'MEIO_EMPREGADO', 
        'GENERO', 'ORIENTACAO_SEXUAL', 'IDADE_VITIMA', 'ESCOLARIDADE_VITIMA', 'RACA_VITIMA'
    ]
    
    # Se for um dashboard customizado, usa as colunas salvas nos metadados
    if dashboard_id:
        dashboards_dir = os.path.join(BASE_DIR, 'dashboards')
        metadata_path = os.path.join(dashboards_dir, f"{dashboard_id}.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            filterable_columns = metadata.get("filterable_columns", filterable_columns)

    schema = {}
    for col in filterable_columns:
        if col in df.columns:
            unique_values = df[col].dropna().unique().tolist()
            try:
                schema[col] = sorted(unique_values)
            except TypeError:
                schema[col] = unique_values
                
    return jsonify(schema)

@app.route('/api/map_data/<string:view_type>', methods=['POST'])
def get_map_data(view_type):
    # 1. IDENTIFICA O DASHBOARD E CARREGA O DATAFRAME CORRETO
    dashboard_id = request.args.get('dashboard_id')
    df_crimes_raw = get_dataframe(dashboard_id) # Usa a função auxiliar que criamos

    # 2. APLICA OS FILTROS DA SIDEBAR
    filters = request.get_json()
    df_filtered = apply_filters(df_crimes_raw, filters) # Sua função de filtro existente

    # 3. LÓGICA DE VISUALIZAÇÃO (seu código original, agora usando os dataframes corretos)
    try:
        if view_type == 'municipality':
            if df_filtered.empty:
                # Retorna o mapa vazio, mas com as geometrias
                empty_gdf = gdf_municipios_raw.copy()
                empty_gdf['QUANTIDADE'] = 0
                empty_gdf['TAXA_POR_100K'] = 0
                empty_gdf['ranking'] = 0
                return jsonify({
                    'geojson': json.loads(empty_gdf.to_json()), 
                    'max_taxa': 0, 
                    'taxa_media_estado': 0, 
                    'total_municipios': len(df_populacao)
                })

            crime_counts = df_filtered.groupby('MUNICIPIO').size().reset_index(name='QUANTIDADE')
            merged_df = pd.merge(df_populacao, crime_counts, left_on='municipio', right_on='MUNICIPIO', how='left').drop(columns=['MUNICIPIO'])
            merged_df['QUANTIDADE'] = merged_df['QUANTIDADE'].fillna(0).astype(int)
            
            merged_df['TAXA_POR_100K'] = 0.0
            mask_pop_valida = merged_df['populacao'] > 0
            merged_df.loc[mask_pop_valida, 'TAXA_POR_100K'] = (merged_df.loc[mask_pop_valida, 'QUANTIDADE'] / merged_df.loc[mask_pop_valida, 'populacao']) * 100000
            
            merged_df_sorted = merged_df.sort_values(by='TAXA_POR_100K', ascending=False).reset_index(drop=True)
            merged_df_sorted['ranking'] = merged_df_sorted.index + 1
            
            # Calcula a média apenas para municípios com população > 0 para evitar distorções
            taxa_media_estado = merged_df_sorted[merged_df_sorted['populacao'] > 0]['TAXA_POR_100K'].mean()
            
            merged_df = pd.merge(merged_df, merged_df_sorted[['municipio', 'ranking']], on='municipio', how='left')
            
            # Usa o gdf_municipios_raw que deve estar carregado globalmente
            geo_df_merged = gdf_municipios_raw.merge(merged_df, left_on='name', right_on='municipio', how='left').fillna(0)
            max_taxa = geo_df_merged['TAXA_POR_100K'].max()

            return jsonify({
                'geojson': json.loads(geo_df_merged.to_json()),
                'max_taxa': max_taxa if pd.notna(max_taxa) else 0,
                'taxa_media_estado': taxa_media_estado if pd.notna(taxa_media_estado) else 0,
                'total_municipios': len(merged_df)
            })

        elif view_type == 'ais':
            if df_filtered.empty:
                empty_gdf = gdf_ais.copy()
                empty_gdf['QUANTIDADE'] = 0
                empty_gdf['TAXA_POR_100K'] = 0
                return jsonify({'geojson': json.loads(empty_gdf.to_json()), 'max_taxa': 0})

            # Certifique-se que o 'municipios_ais_map' está disponível
            df_filtered['AIS_MAPEADA'] = df_filtered['MUNICIPIO'].map(municipios_ais_map)
            crimes_agregados_ais = df_filtered.groupby('AIS_MAPEADA').size().reset_index(name='QUANTIDADE')
            
            # Certifique-se que o 'pop_por_ais' está disponível
            crimes_com_pop_ais = pd.merge(crimes_agregados_ais, pop_por_ais, left_on='AIS_MAPEADA', right_on='AIS', how='left')
            crimes_com_pop_ais.dropna(subset=['populacao'], inplace=True)
            
            crimes_com_pop_ais['TAXA_POR_100K'] = 0.0
            mask_pop_valida_ais = crimes_com_pop_ais['populacao'] > 0
            crimes_com_pop_ais.loc[mask_pop_valida_ais, 'TAXA_POR_100K'] = (crimes_com_pop_ais.loc[mask_pop_valida_ais, 'QUANTIDADE'] / crimes_com_pop_ais.loc[mask_pop_valida_ais, 'populacao']) * 100000

            # Certifique-se que o 'gdf_ais' está disponível
            mapa_completo = gdf_ais.merge(crimes_com_pop_ais, left_on='AIS', right_on='AIS_MAPEADA', how='left').fillna(0)
            max_taxa = mapa_completo['TAXA_POR_100K'].max()
            
            return jsonify({'geojson': json.loads(mapa_completo.to_json()), 'max_taxa': max_taxa if pd.notna(max_taxa) else 0})

        elif view_type == 'heatmap':
            # Verifica se as colunas de latitude/longitude existem no dataframe carregado
            if 'LATITUDE' not in df_filtered.columns or 'LONGITUDE' not in df_filtered.columns:
                return jsonify([]) # Retorna vazio se não houver dados de geolocalização

            df_com_local = df_filtered.dropna(subset=['LATITUDE', 'LONGITUDE'])
            if df_com_local.empty:
                return jsonify([])
            
            points = df_com_local[['LATITUDE', 'LONGITUDE']].values.tolist()
            return jsonify(points)

        return jsonify({"error": "Tipo de visualização inválido"}), 400

    except Exception as e:
        # Log detalhado do erro no servidor para depuração
        import traceback
        print(f"ERRO DETALHADO na rota get_map_data (view: {view_type}, dash_id: {dashboard_id}):")
        print(traceback.format_exc())
        return jsonify({"error": f"Erro interno no servidor: {str(e)}"}), 500

@app.route('/api/correlation_data')
def get_correlation_data():
    crime1 = request.args.get('crime1')
    crime2 = request.args.get('crime2')

    if not crime1 or not crime2:
        return jsonify({"error": "Dois crimes devem ser fornecidos"}), 400

    df_filtered = df_crimes_graficos[df_crimes_graficos['NATUREZA'].isin([crime1, crime2])]

    if df_filtered.empty:
        return jsonify([])

    yearly_counts = df_filtered.groupby(['ANO', 'NATUREZA']).size().unstack(fill_value=0)

    if crime1 not in yearly_counts.columns:
        yearly_counts[crime1] = 0
    if crime2 not in yearly_counts.columns:
        yearly_counts[crime2] = 0
        
    scatter_data = []
    for year, row in yearly_counts.iterrows():
        scatter_data.append({
            'x': int(row[crime1]), 
            'y': int(row[crime2]),
            'year': int(year) 
        })
        
    return jsonify(scatter_data)

@app.route('/api/municipalities')
def get_municipalities():
    municipalities_list = []
    for index, row in municipios_com_centroide.iterrows():
        municipalities_list.append({
            'name': row['name'],
            'lat': row['centroid'].y,
            'lon': row['centroid'].x
        })
    return jsonify(municipalities_list)

@app.route('/api/analyze_csv', methods=['POST'])
def analyze_csv():
    # Verifica se o arquivo foi enviado na requisição
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']

    # Verifica se o nome do arquivo está vazio
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    # Verifica se o arquivo é um CSV
    if file and file.filename.endswith('.csv'):
        try:
            # Lê o CSV diretamente do objeto de arquivo em memória
            df = pd.read_csv(file)
            
            # Pega a lista de nomes das colunas
            column_names = df.columns.tolist()
            
            # Retorna a lista de colunas como JSON
            return jsonify({"columns": column_names})
        
        except Exception as e:
            # Retorna um erro se o Pandas não conseguir ler o arquivo
            return jsonify({"error": f"Erro ao processar o arquivo CSV: {str(e)}"}), 500
    
    return jsonify({"error": "Formato de arquivo inválido. Por favor, envie um .csv"}), 400

@app.route('/api/history/municipio/<nome_municipio>', methods=['POST'])
def get_history_for_municipio(nome_municipio):
    dashboard_id = request.args.get('dashboard_id')
    df_base = get_dataframe(dashboard_id)
    
    filters = request.get_json()
    
    # APLICAÇÃO CORRETA DOS FILTROS
    df_filtered = apply_filters(df_base, filters)
    
    # Garante que a coluna de agrupamento exista
    if 'ANO' not in df_filtered.columns and 'DATA' in df_filtered.columns:
        df_filtered['ANO'] = df_filtered['DATA'].dt.year
    elif 'ANO' not in df_filtered.columns:
         return jsonify({'labels': [], 'data': []}) # Não pode agrupar sem ano

    # Filtra para o município específico
    df_hist = df_filtered[df_filtered['MUNICIPIO'] == nome_municipio]
    
    if df_hist.empty:
        return jsonify({'labels': [], 'data': []})

    history_counts = df_hist.groupby('ANO').size()
    
    start_year = int(df_filtered['ANO'].min())
    end_year = int(df_filtered['ANO'].max())
    full_year_range = pd.RangeIndex(start=start_year, stop=end_year + 1, name='year')
    
    history_counts = history_counts.reindex(full_year_range, fill_value=0)
    
    return jsonify({
        'labels': history_counts.index.tolist(),
        'data': history_counts.values.tolist()
    }) 

@app.route('/api/create_dashboard', methods=['POST'])
def create_dashboard():
    # --- 1. Recebe os dados do formulário ---
    # Dados de texto (nome, descrição, colunas)
    dashboard_name = request.form.get('name')
    dashboard_desc = request.form.get('description')
    selected_columns_json = request.form.get('columns')
    
    # Arquivo CSV
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo CSV enviado"}), 400
    
    file = request.files['file']

    if not dashboard_name or not selected_columns_json or file.filename == '':
        return jsonify({"error": "Dados incompletos"}), 400

    # --- 2. Salva o arquivo CSV ---
    # Cria um nome de arquivo seguro para evitar conflitos e problemas de segurança
    from werkzeug.utils import secure_filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{secure_filename(file.filename)}"
    
    # Garante que a pasta 'uploads' exista
    uploads_dir = os.path.join(BASE_DIR, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    file_path = os.path.join(uploads_dir, safe_filename)
    file.save(file_path)

    # --- 3. Cria e salva o arquivo de metadados (.json) ---
    selected_columns = json.loads(selected_columns_json)
    
    dashboard_id = f"dash_{timestamp}" # ID único para o dashboard
    
    metadata = {
        "id": dashboard_id,
        "name": dashboard_name,
        "description": dashboard_desc,
        "csv_path": file_path, # Caminho absoluto para o CSV
        "filterable_columns": selected_columns
    }
    
    # Garante que a pasta 'dashboards' exista
    dashboards_dir = os.path.join(BASE_DIR, 'dashboards')
    os.makedirs(dashboards_dir, exist_ok=True)
    
    metadata_path = os.path.join(dashboards_dir, f"{dashboard_id}.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

    # --- 4. Retorna uma resposta de sucesso ---
    return jsonify({
        "message": "Dashboard criado com sucesso!",
        "dashboard_id": dashboard_id,
        "dashboard_info": metadata
    }), 201 # 201 Created

@app.route('/api/dashboards/<string:dashboard_id>', methods=['DELETE'])
def delete_dashboard(dashboard_id):
    # O resto da sua função continua igual...
    dashboards_dir = os.path.join(BASE_DIR, 'dashboards')
    metadata_filename = f"{dashboard_id}.json"
    metadata_path = os.path.join(dashboards_dir, metadata_filename)

    # 1. Verifica se o arquivo de metadados existe
    if not os.path.exists(metadata_path):
        return jsonify({"error": "Dashboard não encontrado"}), 404

    try:
        # 2. Lê o arquivo de metadados para encontrar o caminho do CSV
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        csv_path = metadata.get("csv_path")

        # 3. Exclui o arquivo CSV, se o caminho existir
        if csv_path and os.path.exists(csv_path):
            os.remove(csv_path)
        
        # 4. Exclui o arquivo de metadados .json
        os.remove(metadata_path)

        return jsonify({"message": f"Dashboard '{metadata.get('name')}' excluído com sucesso."})

    except Exception as e:
        print(f"Erro ao excluir o dashboard {dashboard_id}: {e}")
        return jsonify({"error": f"Erro interno ao excluir o dashboard: {str(e)}"}), 500

@app.route('/api/dashboards', methods=['GET'])
def list_dashboards():
    dashboards_dir = os.path.join(BASE_DIR, 'dashboards')
    
    # Garante que o diretório exista para não dar erro na primeira execução
    if not os.path.exists(dashboards_dir):
        return jsonify([])

    dashboards = []
    for filename in os.listdir(dashboards_dir):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(dashboards_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Adiciona apenas as informações necessárias para a lista
                    dashboards.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "description": data.get("description")
                    })
            except Exception as e:
                print(f"Erro ao ler o arquivo de metadados {filename}: {e}")

    # Ordena os dashboards pelo nome
    sorted_dashboards = sorted(dashboards, key=lambda d: d['name'])
    
    return jsonify(sorted_dashboards)

@app.route('/api/year_range')
def get_year_range():
    """Retorna o ano mínimo e máximo presentes no dataset."""
    min_year = int(df_crimes_graficos['ANO'].min())
    max_year = int(df_crimes_graficos['ANO'].max())
    return jsonify({'min_year': min_year, 'max_year': max_year})

@app.route('/api/columns')
def get_columns():
    dashboard_id = request.args.get('dashboard_id')
    df = get_dataframe(dashboard_id)
    
    columns_with_types = []
    for col_name in df.columns:
        col_type = 'categorical' # Padrão
        try:
            series = df[col_name].dropna()
            if series.empty:
                columns_with_types.append({'name': col_name, 'type': 'categorical'})
                continue

            # 1. Verifica se é puramente numérico
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                col_type = 'numeric'
            else:
                # 2. Tenta converter para datetime
                datetime_series = pd.to_datetime(series, errors='coerce')
                if datetime_series.notna().all(): # Se TODAS as linhas puderem ser convertidas
                    
                    # --- LÓGICA CORRIGIDA ---
                    # Se o número de dias únicos for maior que 1, é uma coluna de data.
                    # Se for 1, significa que todas as datas são no mesmo dia (provavelmente uma coluna de hora).
                    if datetime_series.dt.normalize().nunique() > 1:
                        col_type = 'date'
                    else:
                        col_type = 'categorical' # É apenas hora, então tratamos como categoria
                # Se não puder ser convertida para datetime, permanece 'categorical'
        except Exception:
            pass
        
        columns_with_types.append({'name': col_name, 'type': col_type})
        
    return jsonify(columns_with_types)

@app.route('/api/generic_chart', methods=['POST'])
def get_generic_chart_data():
    # 1. Pega a configuração do gráfico e os filtros do corpo da requisição
    config = request.get_json()
    chart_type = config.get('chartType')
    column_map = config.get('columnMap')
    filters = config.get('filters')
    dashboard_id = request.args.get('dashboard_id')

    # 2. Carrega o dataframe correto e aplica os filtros da sidebar
    df_base = get_dataframe(dashboard_id)
    df_filtered = apply_filters(df_base, filters)

    try:
        # 3. Lógica para cada tipo de gráfico
        if chart_type == 'bar':
            category_col = column_map.get('category_axis')
            segment_by_col = column_map.get('segment_by') # Pega a coluna opcional

            if not category_col or category_col not in df_filtered.columns:
                raise ValueError(f"Coluna de categoria '{category_col}' não encontrada.")

            # CASO 1: Gráfico de Barras Simples (sem segmentação)
            if not segment_by_col:
                data_counts = df_filtered[category_col].value_counts().nlargest(20)
                labels = [str(l) for l in data_counts.index.tolist()]
                data = data_counts.values.tolist()
                return jsonify({
                    'labels': labels,
                    'datasets': [{'label': f'Contagem de {category_col}', 'data': data}]
                })

            # CASO 2: Gráfico de Barras Agrupado (com segmentação)
            else:
                if segment_by_col not in df_filtered.columns:
                    raise ValueError(f"Coluna de segmentação '{segment_by_col}' não encontrada.")
                
                df_temp = df_filtered.dropna(subset=[category_col, segment_by_col])

                top_main_categories = df_temp[category_col].value_counts().nlargest(15).index
                df_temp = df_temp[df_temp[category_col].isin(top_main_categories)]

                data_grouped = df_temp.groupby([category_col, segment_by_col]).size().unstack(fill_value=0)
                
                labels = [str(l) for l in data_grouped.index.tolist()]
                datasets = []
                
                top_segment_categories = data_grouped.sum().nlargest(7).index

                for cat in top_segment_categories:
                    datasets.append({
                        'label': str(cat),
                        'data': data_grouped[cat].tolist()
                    })
                
                return jsonify({'labels': labels, 'datasets': datasets})

        # --- AQUI ADICIONAREMOS A LÓGICA PARA OUTROS TIPOS DE GRÁFICO (pie, timeseries, etc.) NO FUTURO ---

        else:
            return jsonify({"error": f"Tipo de gráfico '{chart_type}' não suportado."}), 400

    except Exception as e:
        import traceback
        print(f"ERRO ao gerar gráfico genérico: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)