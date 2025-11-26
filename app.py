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

def get_filtered_df_for_charts():
    genero_filtro = request.args.get('genero')
    df_filtrado = df_crimes_graficos.copy()
    if genero_filtro == 'feminino':
        df_filtrado = df_filtrado[df_filtrado['GENERO_AGRUPADO'] == 'Feminino']
    return df_filtrado

@app.route('/')
def index():
    return render_template('index.html', crimes=LISTA_DE_CRIMES)

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

@app.route('/api/municipality_map_data')
def get_municipality_map_data():
    selected_crimes = request.args.get('crimes').split(',')
    ano_inicio = int(request.args.get('ano_inicio'))
    ano_fim = int(request.args.get('ano_fim'))
    df_periodo = df_crimes_raw[
        (df_crimes_raw['DATA'].dt.year >= ano_inicio) &
        (df_crimes_raw['DATA'].dt.year <= ano_fim)
    ]
    df_filtered = df_periodo[df_periodo['NATUREZA'].isin(selected_crimes)]
    crime_counts = df_filtered.groupby('MUNICIPIO').size().reset_index(name='QUANTIDADE')
    merged_df = pd.merge(df_populacao, crime_counts, left_on='municipio', right_on='MUNICIPIO', how='left').drop(columns=['MUNICIPIO'])
    merged_df['QUANTIDADE'] = merged_df['QUANTIDADE'].fillna(0).astype(int)
    merged_df['TAXA_POR_100K'] = 0.0
    mask_pop_valida = merged_df['populacao'] > 0
    merged_df.loc[mask_pop_valida, 'TAXA_POR_100K'] = \
        (merged_df.loc[mask_pop_valida, 'QUANTIDADE'] / merged_df.loc[mask_pop_valida, 'populacao']) * 100000
    merged_df_sorted = merged_df.sort_values(by='TAXA_POR_100K', ascending=False).reset_index(drop=True)
    merged_df_sorted['ranking'] = merged_df_sorted.index + 1
    taxa_media_estado = merged_df_sorted[merged_df_sorted['populacao'] > 0]['TAXA_POR_100K'].mean()
    merged_df = pd.merge(merged_df, merged_df_sorted[['municipio', 'ranking']], on='municipio', how='left')
    geo_df_merged = gdf_municipios_raw.merge(merged_df, left_on='name', right_on='municipio', how='left')
    geo_df_merged = geo_df_merged.fillna(0)
    max_taxa = geo_df_merged['TAXA_POR_100K'].max()

    return jsonify({
        'geojson': json.loads(geo_df_merged.to_json()),
        'max_taxa': max_taxa,
        'taxa_media_estado': taxa_media_estado,
        'total_municipios': len(merged_df)
    })


@app.route('/api/ais_map_data')
def get_ais_map_data():
    crime_types_str = request.args.get('crimes')
    if not crime_types_str:
        return jsonify({"error": "Nenhum crime selecionado"}), 400
    crime_types = crime_types_str.split(',')

    dados_filtrados = crimes_com_pop_ais[crimes_com_pop_ais['NATUREZA'].isin(crime_types)]

    dados_agregados = dados_filtrados.groupby('AIS_MAPEADA').agg({
        'QUANTIDADE': 'sum',
        'populacao': 'first'
    }).reset_index()

    dados_agregados['TAXA_POR_100K'] = (dados_agregados['QUANTIDADE'] / dados_agregados['populacao']) * 100000

    mapa_completo = gdf_ais.merge(dados_agregados, left_on='AIS', right_on='AIS_MAPEADA', how='left')
    mapa_completo[['QUANTIDADE', 'TAXA_POR_100K']] = mapa_completo[['QUANTIDADE', 'TAXA_POR_100K']].fillna(0)
    max_taxa = mapa_completo['TAXA_POR_100K'].max()
    
    return jsonify({'geojson': json.loads(mapa_completo.to_json()), 'max_taxa': max_taxa})

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

@app.route('/api/history/municipio/<nome_municipio>')
def get_history_for_municipio(nome_municipio):
    selected_crimes = request.args.get('crimes').split(',')
    
    df_hist = df_crimes_graficos[(df_crimes_graficos['MUNICIPIO'] == nome_municipio) & (df_crimes_graficos['NATUREZA'].isin(selected_crimes))]
    
    if df_hist.empty:
        return jsonify({'labels': [], 'data': []})

    history_counts = df_hist.groupby(df_hist['DATA'].dt.year).size()
    
    all_years = df_crimes_graficos['DATA'].dt.year.dropna().unique()
    min_year, max_year = int(all_years.min()), int(all_years.max())
    full_year_range = pd.RangeIndex(start=min_year, stop=max_year + 1, name='year')
    
    history_counts = history_counts.reindex(full_year_range, fill_value=0)
    
    return jsonify({
        'labels': history_counts.index.tolist(),
        'data': history_counts.values.tolist()
    })

@app.route('/api/data/grafico_evolucao_anual')
def get_data_grafico_evolucao_anual():
    df_filtrado = get_filtered_df_for_charts()
    try:
        predict_years = int(request.args.get('predict', 0))
    except (ValueError, TypeError):
        predict_years = 0
    
    df_analise = df_filtrado.dropna(subset=['ANO', 'MES', 'GENERO_AGRUPADO'])
    df_analise = df_analise[pd.to_numeric(df_analise['ANO'], errors='coerce').notna()]
    df_analise.loc[:, 'ANO'] = df_analise['ANO'].astype(int)

    dados_agrupados = df_analise.groupby(['ANO', 'MES', 'GENERO_AGRUPADO']).size().reset_index(name='TOTAL')
    
    ano_maximo = int(df_analise['ANO'].max()) if not df_analise.empty else datetime.now().year -1
    hoje = datetime.now()
    is_projected = False

    if ano_maximo == hoje.year and hoje.month < 12:
        is_projected = True
        ultimo_mes = int(df_analise[df_analise['ANO'] == ano_maximo]['MES'].max())
        df_projetado = projetar_ano_incompleto(dados_agrupados, ano_maximo, ultimo_mes, ['GENERO_AGRUPADO'])
        dados_finais = dados_agrupados[dados_agrupados['ANO'] < ano_maximo].groupby(['ANO', 'GENERO_AGRUPADO'])['TOTAL'].sum().reset_index()
        df_projetado['ANO'] = ano_maximo
        dados_finais = pd.concat([dados_finais, df_projetado], ignore_index=True)
    else:
        dados_finais = dados_agrupados.groupby(['ANO', 'GENERO_AGRUPADO'])['TOTAL'].sum().reset_index()

    dados_pivot = dados_finais.pivot(index='ANO', columns='GENERO_AGRUPADO', values='TOTAL').fillna(0)
    labels = [str(int(ano)) for ano in dados_pivot.index.tolist()]
    if is_projected:
        labels[-1] = f"{labels[-1]} (Projetado)"

    datasets = []
    if 'Masculino' in dados_pivot:
        datasets.append({'label': 'Masculino', 'data': dados_pivot['Masculino'].tolist(), 'borderColor': 'rgba(54, 162, 235, 1)'})
    if 'Feminino' in dados_pivot:
        datasets.append({'label': 'Feminino', 'data': dados_pivot['Feminino'].tolist(), 'borderColor': 'rgba(255, 99, 132, 1)'})

    if predict_years > 0 and not dados_pivot.empty:
        anos_historicos = dados_pivot.index.values.reshape(-1, 1)
        anos_futuros = np.arange(ano_maximo + 1, ano_maximo + 1 + predict_years).reshape(-1, 1)
        
        for i, dataset in enumerate(datasets):
            genero = dataset['label']
            if genero in dados_pivot:
                model = LinearRegression().fit(anos_historicos, dados_pivot[genero].values)
                previsao = model.predict(anos_futuros).round(0).astype(int)
                previsao[previsao < 0] = 0
                datasets[i]['data'].extend(previsao.tolist())

        for ano in anos_futuros.flatten():
            labels.append(f"{ano} (Previsão)")
            
    return jsonify({'labels': labels, 'datasets': datasets})

@app.route('/api/data/grafico_comparativo_idade_genero')
def get_data_grafico_comparativo_idade_genero():
    df_filtrado = get_filtered_df_for_charts()
    df_idade = df_filtrado.copy()
    df_idade['IDADE_NUM'] = pd.to_numeric(df_idade['IDADE_VITIMA'], errors='coerce')
    df_idade.dropna(subset=['IDADE_NUM', 'GENERO_AGRUPADO'], inplace=True)
    df_idade['IDADE_NUM'] = df_idade['IDADE_NUM'].astype(int)
    df_idade = df_idade[(df_idade['IDADE_NUM'] >= 0) & (df_idade['IDADE_NUM'] <= 110)]
    
    if df_idade.empty:
        return jsonify({'labels': [], 'datasets': []})

    dados_grafico = df_idade.groupby(['IDADE_NUM', 'GENERO_AGRUPADO']).size().unstack(fill_value=0)
    if 'Masculino' not in dados_grafico: dados_grafico['Masculino'] = 0
    if 'Feminino' not in dados_grafico: dados_grafico['Feminino'] = 0
    dados_grafico = dados_grafico.reindex(range(111), fill_value=0)
    
    return jsonify({
        'labels': dados_grafico.index.tolist(),
        'datasets': [
            {'label': 'Masculino', 'data': dados_grafico['Masculino'].tolist(), 'borderColor': 'rgba(54, 162, 235, 1)', 'backgroundColor': 'rgba(54, 162, 235, 0.5)', 'fill': True, 'tension': 0.4},
            {'label': 'Feminino', 'data': dados_grafico['Feminino'].tolist(), 'borderColor': 'rgba(255, 99, 132, 1)', 'backgroundColor': 'rgba(255, 99, 132, 0.5)', 'fill': True, 'tension': 0.4}
        ]
    })

@app.route('/api/data/grafico_crimes_mulher_dia_hora')
def get_data_grafico_crimes_mulher_dia_hora():
    df_feminino = df_crimes_graficos[df_crimes_graficos['GENERO_AGRUPADO'] == 'Feminino'].copy()
    if df_feminino.empty: return jsonify({'labels': [], 'datasets': []})
    df_feminino['HORA_NUM'] = pd.to_datetime(df_feminino['HORA'], format='%H:%M:%S', errors='coerce').dt.hour
    df_feminino.dropna(subset=['HORA_NUM'], inplace=True)
    df_feminino['HORA_NUM'] = df_feminino['HORA_NUM'].astype(int)
    ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    df_feminino['DIA_SEMANA'] = pd.Categorical(df_feminino['DIA_SEMANA'], categories=ordem_dias, ordered=True)
    crimes_por_dia_hora = df_feminino.groupby(['DIA_SEMANA', 'HORA_NUM'], observed=False).size().unstack(fill_value=0)
    datasets = []
    cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF']
    for i, dia in enumerate(ordem_dias):
        if dia in crimes_por_dia_hora.index:
            datasets.append({'label': dia, 'data': crimes_por_dia_hora.loc[dia].reindex(range(24), fill_value=0).tolist(), 'borderColor': cores[i], 'backgroundColor': cores[i], 'fill': False, 'tension': 0.1})
    return jsonify({'labels': list(range(24)), 'datasets': datasets})

@app.route('/api/year_range')
def get_year_range():
    """Retorna o ano mínimo e máximo presentes no dataset."""
    min_year = int(df_crimes_graficos['ANO'].min())
    max_year = int(df_crimes_graficos['ANO'].max())
    return jsonify({'min_year': min_year, 'max_year': max_year})

@app.route('/api/data/grafico_distribuicao_raca')
def get_data_grafico_distribuicao_raca():
    df_filtrado = get_filtered_df_for_charts()
    df_raca = df_filtrado[df_filtrado['RACA_VITIMA'] != 'NÃO INFORMADA'].copy()
    if df_raca.empty: return jsonify({'labels': [], 'datasets': []})
    contagem_raca = df_raca['RACA_VITIMA'].value_counts()
    return jsonify({'labels': contagem_raca.index.tolist(), 'datasets': [{'label': 'Total de Vítimas', 'data': contagem_raca.values.tolist(), 'backgroundColor': ['#440154', '#482878', '#3e4a89', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6dcd59', '#b4de2c', '#fde725']}]})

@app.route('/api/data/grafico_densidade_etaria')
def get_data_grafico_densidade_etaria():
    df_filtrado = get_filtered_df_for_charts()
    df_idade = df_filtrado.copy()
    df_idade['IDADE_NUM'] = pd.to_numeric(df_idade['IDADE_VITIMA'], errors='coerce')
    df_idade.dropna(subset=['IDADE_NUM'], inplace=True)
    df_idade['IDADE_NUM'] = df_idade['IDADE_NUM'].astype(int)
    df_idade = df_idade[(df_idade['IDADE_NUM'] >= 0) & (df_idade['IDADE_NUM'] <= 110)]
    if df_idade.empty: return jsonify({'labels': [], 'datasets': []})
    contagem_por_idade = df_idade.groupby('IDADE_NUM').size().reindex(range(111), fill_value=0)
    return jsonify({'labels': contagem_por_idade.index.tolist(), 'datasets': [{'label': 'Número de Vítimas', 'data': contagem_por_idade.values.tolist(), 'borderColor': 'rgba(75, 192, 192, 1)', 'backgroundColor': 'rgba(75, 192, 192, 0.5)', 'fill': True, 'tension': 0.4}]})

@app.route('/api/data/grafico_comparativo_crime_log')
def get_data_grafico_3a():
    df_analise = df_crimes_graficos.dropna(subset=['GENERO_AGRUPADO', 'NATUREZA'])
    crimes_por_natureza = df_analise.groupby(['NATUREZA', 'GENERO_AGRUPADO']).size().unstack(fill_value=0)
    crimes_por_natureza['TOTAL'] = crimes_por_natureza.sum(axis=1)
    crimes_por_natureza = crimes_por_natureza.sort_values('TOTAL', ascending=False)
    datasets = []
    if 'Masculino' in crimes_por_natureza:
        datasets.append({'label': 'Masculino', 'data': crimes_por_natureza['Masculino'].tolist(), 'backgroundColor': 'rgba(54, 162, 235, 0.7)'})
    if 'Feminino' in crimes_por_natureza:
        datasets.append({'label': 'Feminino', 'data': crimes_por_natureza['Feminino'].tolist(), 'backgroundColor': 'rgba(255, 99, 132, 0.7)'})
    return jsonify({'labels': crimes_por_natureza.index.tolist(), 'datasets': datasets})

@app.route('/api/data/grafico_proporcao_genero_crime')
def get_data_grafico_3b():
    df_analise = df_crimes_graficos.dropna(subset=['GENERO_AGRUPADO', 'NATUREZA'])
    crimes_por_natureza = df_analise.groupby(['NATUREZA', 'GENERO_AGRUPADO']).size().reset_index(name='QUANTIDADE')
    total_por_natureza = crimes_por_natureza.groupby('NATUREZA')['QUANTIDADE'].transform('sum')
    crimes_por_natureza['PROPORCAO_%'] = (crimes_por_natureza['QUANTIDADE'] / total_por_natureza) * 100
    df_pivot = crimes_por_natureza.pivot(index='NATUREZA', columns='GENERO_AGRUPADO', values='PROPORCAO_%').fillna(0)
    df_pivot['TOTAL'] = df_pivot.sum(axis=1)
    df_pivot = df_pivot.sort_values('TOTAL', ascending=True)
    datasets = []
    if 'Masculino' in df_pivot:
        datasets.append({'label': 'Masculino', 'data': df_pivot['Masculino'].tolist(), 'backgroundColor': 'rgba(54, 162, 235, 0.7)'})
    if 'Feminino' in df_pivot:
        datasets.append({'label': 'Feminino', 'data': df_pivot['Feminino'].tolist(), 'backgroundColor': 'rgba(255, 99, 132, 0.7)'})
    return jsonify({'labels': df_pivot.index.tolist(), 'datasets': datasets})

def get_meio_empregado_df(filtro_genero='todos'):
    df_filtrado = df_crimes_graficos.copy()
    if filtro_genero == 'feminino':
        df_filtrado = df_filtrado[df_filtrado['GENERO_AGRUPADO'] == 'Feminino']
    df_meio = df_filtrado.dropna(subset=['MEIO_EMPREGADO'])
    df_meio = df_meio[df_meio['MEIO_EMPREGADO'] != 'NÃO INFORMADO'].copy()
    return df_meio

@app.route('/api/data/grafico_proporcao_meio_empregado')
def get_data_grafico_6a():
    filtro = request.args.get('filtro', 'todos')
    df_meio = get_meio_empregado_df(filtro)
    if df_meio.empty: return jsonify({'labels': [], 'datasets': []})
    contagem_meio = df_meio['MEIO_EMPREGADO'].value_counts()
    return jsonify({
        'labels': contagem_meio.index.tolist(),
        'datasets': [{'label': 'Meio Empregado', 'data': contagem_meio.values.tolist(), 'backgroundColor': ['#440154', '#482878', '#3e4a89', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6dcd59', '#b4de2c', '#fde725']}]
    })

@app.route('/api/data/grafico_evolucao_meio_empregado')
def get_data_grafico_6b():
    filtro = request.args.get('filtro', 'todos')
    df_meio = get_meio_empregado_df(filtro)
    if df_meio.empty: return jsonify({'labels': [], 'datasets': []})
    df_meio = df_meio.dropna(subset=['ANO'])
    df_meio['ANO'] = df_meio['ANO'].astype(int)
    evolucao_meio = df_meio.groupby(['ANO', 'MEIO_EMPREGADO']).size().unstack(fill_value=0)
    datasets = []
    cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#440154', '#21908d', '#fde725']
    for i, meio in enumerate(evolucao_meio.columns):
        datasets.append({'label': meio, 'data': evolucao_meio[meio].tolist(), 'borderColor': cores[i % len(cores)], 'fill': False, 'tension': 0.1})
    return jsonify({'labels': [str(int(ano)) for ano in evolucao_meio.index.tolist()], 'datasets': datasets})

@app.route('/api/data/grafico_evolucao_odio')
def get_data_grafico_7a():
    df_filtrado = get_filtered_df_for_charts()
    naturezas_odio = ['CONDUTA HOMOFOBICA', 'CONDUTA TRANSFOBICA', 'PRECONCEITO RAÇA OU COR']
    df_odio = df_filtrado[df_filtrado['NATUREZA'].isin(naturezas_odio)].copy()
    if df_odio.empty or 'ANO' not in df_odio.columns: return jsonify({'labels': [], 'datasets': []})
    df_odio = df_odio.dropna(subset=['ANO'])
    df_odio['ANO'] = df_odio['ANO'].astype(int)
    evolucao_odio = df_odio.groupby(['ANO', 'NATUREZA']).size().unstack(fill_value=0)
    datasets = []
    cores = {'CONDUTA HOMOFOBICA': '#E41A1C', 'CONDUTA TRANSFOBICA': '#377EB8', 'PRECONCEITO RAÇA OU COR': '#4DAF4A'}
    for natureza in evolucao_odio.columns:
        if natureza in cores:
            datasets.append({'label': natureza, 'data': evolucao_odio[natureza].tolist(), 'borderColor': cores.get(natureza, '#000000'), 'fill': False, 'tension': 0.1})
    return jsonify({'labels': [str(int(ano)) for ano in evolucao_odio.index.tolist()], 'datasets': datasets})

@app.route('/api/data/grafico_perfil_orientacao_sexual')
def get_data_grafico_7b():
    df_filtrado = get_filtered_df_for_charts()
    naturezas_lgbtfobia = ['CONDUTA HOMOFOBICA', 'CONDUTA TRANSFOBICA']
    df_lgbtfobia = df_filtrado[df_filtrado['NATUREZA'].isin(naturezas_lgbtfobia)].copy()
    df_lgbtfobia = df_lgbtfobia[df_lgbtfobia['ORIENTACAO_SEXUAL'] != 'NÃO INFORMADO'].copy()
    if df_lgbtfobia.empty: return jsonify({'labels': [], 'datasets': []})
    contagem_orientacao = df_lgbtfobia['ORIENTACAO_SEXUAL'].value_counts()
    return jsonify({
        'labels': contagem_orientacao.index.tolist(),
        'datasets': [{'label': 'Total de Vítimas', 'data': contagem_orientacao.values.tolist(), 'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']}]
    })

@app.route('/api/data/grafico_evolucao_anual_homicidios')
def get_data_grafico_evolucao_anual_homicidios():
    df_filtrado = get_filtered_df_for_charts()
    
    naturezas_homicidio = ['HOMICIDIO DOLOSO', 'FEMINICIDIO', 'LATROCINIO', 'LESAO CORPORAL SEGUIDA DE MORTE']
    df_homicidios = df_filtrado[df_filtrado['NATUREZA'].isin(naturezas_homicidio)]
    
    df_analise = df_homicidios.dropna(subset=['ANO', 'MES', 'GENERO_AGRUPADO']).copy()
    df_analise['ANO'] = pd.to_numeric(df_analise['ANO'], errors='coerce').astype('Int64')
    df_analise.dropna(subset=['ANO'], inplace=True)

    if df_analise.empty:
        return jsonify({'labels': [], 'datasets': []})

    # --- NOVA LÓGICA DE PROJEÇÃO ---
    
    # Agrupa por mês para poder fazer a projeção
    dados_mensais = df_analise.groupby(['ANO', 'MES', 'GENERO_AGRUPADO']).size().reset_index(name='TOTAL')
    
    ano_maximo = int(dados_mensais['ANO'].max())
    hoje = datetime.now()
    is_projected = False

    # Verifica se o ano máximo é o ano corrente e se ele está incompleto
    if ano_maximo == hoje.year and hoje.month < 12:
        is_projected = True
        ultimo_mes_registrado = int(dados_mensais[dados_mensais['ANO'] == ano_maximo]['MES'].max())
        
        # Chama nossa função de projeção
        df_projetado = projetar_ano_incompleto(dados_mensais, ano_maximo, ultimo_mes_registrado, ['GENERO_AGRUPADO'])
        df_projetado['ANO'] = ano_maximo
        
        # Pega os dados dos anos anteriores completos
        dados_finais = dados_mensais[dados_mensais['ANO'] < ano_maximo].groupby(['ANO', 'GENERO_AGRUPADO'])['TOTAL'].sum().reset_index()
        
        # Junta os dados completos com o ano projetado
        dados_finais = pd.concat([dados_finais, df_projetado], ignore_index=True)
    else:
        # Se não precisar de projeção, apenas agrupa por ano
        dados_finais = dados_mensais.groupby(['ANO', 'GENERO_AGRUPADO'])['TOTAL'].sum().reset_index()

    # --- FIM DA LÓGICA DE PROJEÇÃO ---

    dados_pivot = dados_finais.pivot(index='ANO', columns='GENERO_AGRUPADO', values='TOTAL').fillna(0)
    
    labels = [str(int(ano)) for ano in dados_pivot.index.tolist()]
    # Adiciona o sufixo "(Projetado)" ao label do último ano, se for o caso
    if is_projected:
        labels[-1] = f"{labels[-1]} (Projetado)"

    datasets = []
    if 'Masculino' in dados_pivot.columns and request.args.get('genero') != 'feminino':
        datasets.append({
            'label': 'Masculino', 
            'data': dados_pivot['Masculino'].round(0).astype(int).tolist(), # Arredonda os valores projetados
            'borderColor': 'rgba(54, 162, 235, 1)',
            'backgroundColor': 'rgba(54, 162, 235, 0.2)'
        })
        
    if 'Feminino' in dados_pivot.columns and request.args.get('genero') != 'masculino':
        datasets.append({
            'label': 'Feminino', 
            'data': dados_pivot['Feminino'].round(0).astype(int).tolist(), # Arredonda os valores projetados
            'borderColor': 'rgba(255, 99, 132, 1)',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)'
        })
        
    return jsonify({'labels': labels, 'datasets': datasets})
@app.route('/api/data/grafico_densidade_etaria_homicidios')
def get_data_grafico_densidade_etaria_homicidios():
    df_filtrado = get_filtered_df_for_charts() 
    
    naturezas_homicidio = ['HOMICIDIO DOLOSO', 'FEMINICIDIO', 'LATROCINIO', 'LESAO CORPORAL SEGUIDA DE MORTE']
    df_homicidios = df_filtrado[df_filtrado['NATUREZA'].isin(naturezas_homicidio)]

    df_idade = get_clean_age_df(df_homicidios)
    if df_idade.empty: 
        return jsonify({'labels': [], 'datasets': []})
        
    contagem_por_idade = df_idade.groupby('IDADE_NUM').size().reindex(range(111), fill_value=0)
    
    cor_borda = 'rgba(199, 0, 57, 1)' 
    cor_fundo = 'rgba(199, 0, 57, 0.5)'
    if request.args.get('genero') != 'feminino':
        cor_borda = 'rgba(75, 192, 192, 1)'
        cor_fundo = 'rgba(75, 192, 192, 0.5)'

    return jsonify({
        'labels': contagem_por_idade.index.tolist(), 
        'datasets': [{
            'label': 'Número de Vítimas de Homicídio', 
            'data': contagem_por_idade.values.tolist(), 
            'borderColor': cor_borda, 
            'backgroundColor': cor_fundo, 
            'fill': True, 
            'tension': 0.4
        }]
    })


@app.route('/api/data/grafico_proporcao_meio_empregado_homicidios')
def get_data_grafico_proporcao_meio_empregado_homicidios():
    df_filtrado = get_filtered_df_for_charts()
    naturezas_homicidio = ['HOMICIDIO DOLOSO', 'FEMINICIDIO', 'LATROCINIO', 'LESAO CORPORAL SEGUIDA DE MORTE']
    df_homicidios = df_filtrado[df_filtrado['NATUREZA'].isin(naturezas_homicidio)]

    df_meio = df_homicidios.dropna(subset=['MEIO_EMPREGADO'])
    df_meio = df_meio[df_meio['MEIO_EMPREGADO'] != 'NÃO INFORMADO'].copy()
    if df_meio.empty: return jsonify({'labels': [], 'datasets': []})
        
    contagem_meio = df_meio['MEIO_EMPREGADO'].value_counts()
    
    return jsonify({
        'labels': contagem_meio.index.tolist(),
        'datasets': [{'label': 'Meio Empregado', 'data': contagem_meio.values.tolist(), 'backgroundColor': ['#c70039', '#f94c10', '#f8de22', '#73a2c6', '#3d5a80']}]
    })
@app.route('/api/data/grafico_comparativo_idade_genero_homicidios')
def get_data_grafico_comparativo_idade_genero_homicidios():
    df_filtrado = df_crimes_graficos.copy()
    
    naturezas_homicidio = ['HOMICIDIO DOLOSO', 'FEMINICIDIO', 'LATROCINIO', 'LESAO CORPORAL SEGUIDA DE MORTE']
    df_homicidios = df_filtrado[df_filtrado['NATUREZA'].isin(naturezas_homicidio)]

    df_idade = get_clean_age_df(df_homicidios) 
    df_idade.dropna(subset=['GENERO_AGRUPADO'], inplace=True)

    if df_idade.empty:
        return jsonify({'labels': [], 'datasets': []})

    dados_grafico = df_idade.groupby(['IDADE_NUM', 'GENERO_AGRUPADO']).size().unstack(fill_value=0)

    if 'Masculino' not in dados_grafico: dados_grafico['Masculino'] = 0
    if 'Feminino' not in dados_grafico: dados_grafico['Feminino'] = 0
    
    dados_grafico = dados_grafico.reindex(range(111), fill_value=0)
    
    return jsonify({
        'labels': dados_grafico.index.tolist(),
        'datasets': [
            {'label': 'Masculino', 'data': dados_grafico['Masculino'].tolist(), 'borderColor': 'rgba(54, 162, 235, 1)', 'backgroundColor': 'rgba(54, 162, 235, 0.5)', 'fill': True, 'tension': 0.4},
            {'label': 'Feminino', 'data': dados_grafico['Feminino'].tolist(), 'borderColor': 'rgba(255, 99, 132, 1)', 'backgroundColor': 'rgba(255, 99, 132, 0.5)', 'fill': True, 'tension': 0.4}
        ]
    })
@app.route('/api/debug/homicidios_mulheres')
def debug_homicidios_mulheres():
    # 1. Define a lista de naturezas de homicídio
    naturezas_homicidio = ['HOMICIDIO DOLOSO', 'FEMINICIDIO', 'LATROCINIO', 'LESAO CORPORAL SEGUIDA DE MORTE']
    
    # 2. Filtra o DataFrame principal para esses crimes E para o gênero feminino
    df_homicidios_fem = df_crimes_graficos[
        (df_crimes_graficos['NATUREZA'].isin(naturezas_homicidio)) &
        (df_crimes_graficos['GENERO_AGRUPADO'] == 'Feminino')
    ]
    
    # 3. Calcula os totais
    total_vitimas = len(df_homicidios_fem)
    
    # 4. Conta quantos desses registros têm a coluna 'MEIO_EMPREGADO' preenchida e não é 'NÃO INFORMADO'
    contagem_meio_empregado_valido = len(df_homicidios_fem.dropna(subset=['MEIO_EMPREGADO']))
    contagem_meio_empregado_sem_na = len(df_homicidios_fem[df_homicidios_fem['MEIO_EMPREGADO'] != 'NÃO INFORMADO'])

    return jsonify({
        'TOTAL_DE_VITIMAS_DE_HOMICIDIO_FEMININO': total_vitimas,
        'VITIMAS_COM_MEIO_EMPREGADO_PREENCHIDO': contagem_meio_empregado_valido,
        'VITIMAS_COM_MEIO_EMPREGADO_DIFERENTE_DE_NAO_INFORMADO': contagem_meio_empregado_sem_na,
        'PERCENTUAL_DE_DADOS_UTILIZADOS_NO_GRAFICO': f"{(contagem_meio_empregado_sem_na / total_vitimas) * 100 if total_vitimas > 0 else 0:.2f}%"
    })

@app.route('/api/heatmap_map_data')
def get_heatmap_map_data():
    selected_crimes = request.args.get('crimes').split(',')
    ano_inicio = int(request.args.get('ano_inicio'))
    ano_fim = int(request.args.get('ano_fim'))

    # 1. Filtra os dados
    df_periodo = df_crimes_graficos[
        (df_crimes_graficos['ANO'] >= ano_inicio) &
        (df_crimes_graficos['ANO'] <= ano_fim) &
        (df_crimes_graficos['NATUREZA'].isin(selected_crimes))
    ]

    if df_periodo.empty:
        return jsonify([]) # Retorna apenas uma lista vazia

    # 2. Calcula a TAXA por município
    crime_counts = df_periodo.groupby('MUNICIPIO').size().reset_index(name='QUANTIDADE')
    merged_df = pd.merge(df_populacao, crime_counts, left_on='municipio', right_on='MUNICIPIO', how='left')
    merged_df['QUANTIDADE'] = merged_df['QUANTIDADE'].fillna(0)
    merged_df['TAXA_POR_100K'] = 0.0
    mask_pop_valida = merged_df['populacao'] > 0
    merged_df.loc[mask_pop_valida, 'TAXA_POR_100K'] = \
        (merged_df.loc[mask_pop_valida, 'QUANTIDADE'] / merged_df.loc[mask_pop_valida, 'populacao']) * 100000

    # 3. Junta com os centroides
    df_final = pd.merge(municipios_com_centroide, merged_df, left_on='name', right_on='municipio', how='left')
    df_final['TAXA_POR_100K'] = df_final['TAXA_POR_100K'].fillna(0)

    # 4. Prepara os pontos para o heatmap
    points = []
    for _, row in df_final.iterrows():
        if row['centroid'] and not row['centroid'].is_empty and row['TAXA_POR_100K'] > 0:
            points.append([
                row['centroid'].y,
                row['centroid'].x,
                row['TAXA_POR_100K']
            ])
    
    # Retorna APENAS a lista de pontos
    return jsonify(points)
if __name__ == '__main__':
    app.run(debug=True)