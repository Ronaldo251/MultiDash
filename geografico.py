# -*- coding: utf-8 -*-

"""
Análise Geográfica de Crimes no Ceará (v6.0) - Solução Definitiva

Este script baixa os arquivos ZIP oficiais de shapefiles do IBGE (Municípios)
e do Governo do Ceará (AIS) e lê os dados geográficos diretamente deles,
eliminando todas as falhas anteriores com links quebrados e dados incompletos.
"""

import pandas as pd
import geopandas as gpd
import folium
import requests
import os

def baixar_arquivo_zip(url, nome_arquivo_zip):
    """Verifica se um arquivo ZIP existe; se não, faz o download."""
    if not os.path.exists(nome_arquivo_zip):
        print(f"Arquivo '{nome_arquivo_zip}' não encontrado. Baixando de {url}...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            resposta = requests.get(url, headers=headers, timeout=60, stream=True)
            resposta.raise_for_status()
            with open(nome_arquivo_zip, 'wb') as f:
                for chunk in resposta.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Download de '{nome_arquivo_zip}' concluído com sucesso.")
        except requests.exceptions.RequestException as e:
            print(f"ERRO CRÍTICO: Falha ao baixar o arquivo de {url}.")
            print(f"Detalhe do erro: {e}")
            exit()
    else:
        print(f"Arquivo '{nome_arquivo_zip}' já existe localmente.")

# 1. DOWNLOAD E CARREGAMENTO DOS DADOS
print("Verificando e carregando arquivos de dados...")

# URL oficial do IBGE para a malha de municípios do Ceará (2020)
url_municipios_zip = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_politico_administrativas/2020/Malha_de_Municipios_com_Setores_Censitarios/CE/CE_Municipios_2020.zip"
# URL oficial do Ceará Transparente para as AIS
url_ais_zip = "https://cearatransparente.ce.gov.br/documents/118225/355393/ce_ais.zip/c6392a8b-036f-479c-93a0-3c183354452a"

# Nomes dos arquivos ZIP que serão salvos
zip_municipios = "CE_Municipios_2020.zip"
zip_ais = "ce_ais.zip"

baixar_arquivo_zip(url_municipios_zip, zip_municipios )
baixar_arquivo_zip(url_ais_zip, zip_ais)

try:
    df_crimes = pd.read_csv('crimes.csv', sep=';')
    # GeoPandas lê diretamente do arquivo ZIP
    gdf_municipios = gpd.read_file(f"zip://{zip_municipios}")
    gdf_ais = gpd.read_file(f"zip://{zip_ais}")
    print("Arquivos de dados e geográficos carregados com sucesso.")
except Exception as e:
    print(f"Erro ao ler os arquivos. Detalhe: {e}")
    exit()

# 2. PREPARAÇÃO E AGREGAÇÃO DOS DADOS
print("Processando e agregando dados de crimes...")
df_crimes.columns = [
    'AIS', 'NATUREZA', 'MUNICIPIO', 'LOCAL', 'DATA', 'HORA', 'DIA_SEMANA',
    'MEIO_EMPREGADO', 'GENERO', 'ORIENTACAO_SEXUAL', 'IDADE_VITIMA',
    'ESCOLARIDADE_VITIMA', 'RACA_VITIMA'
]

# Normalização para junção de municípios (coluna no shapefile do IBGE: NM_MUN)
df_crimes['MUNICIPIO_NORM'] = df_crimes['MUNICIPIO'].str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
gdf_municipios['NM_MUN_NORM'] = gdf_municipios['NM_MUN'].str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

crimes_por_municipio = df_crimes.groupby(['MUNICIPIO_NORM', 'NATUREZA']).size().reset_index(name='QUANTIDADE')
crimes_por_ais = df_crimes.groupby(['AIS', 'NATUREZA']).size().reset_index(name='QUANTIDADE')

# 3. JUNÇÃO DOS DADOS
print("Juntando dados de crimes com as geometrias...")
mapa_data_municipios = gdf_municipios.merge(
    crimes_por_municipio, left_on='NM_MUN_NORM', right_on='MUNICIPIO_NORM', how='left'
)
mapa_data_municipios['QUANTIDADE'].fillna(0, inplace=True)

# A coluna no shapefile das AIS é 'nome'
mapa_data_ais = gdf_ais.merge(
    crimes_por_ais, left_on='nome', right_on='AIS', how='left'
)
mapa_data_ais['QUANTIDADE'].fillna(0, inplace=True)

# 4. CRIAÇÃO DO MAPA INTERATIVO
print("Criando o mapa interativo com Folium...")
mapa = folium.Map(location=[-5.0, -39.5], zoom_start=7, tiles='CartoDB positron')
lista_de_crimes = sorted(df_crimes['NATUREZA'].dropna().unique().tolist())

for crime in lista_de_crimes:
    # Camada de Municípios
    folium.Choropleth(
        geo_data=mapa_data_municipios[mapa_data_municipios['NATUREZA'] == crime],
        name=f"Municípios - {crime}", data=mapa_data_municipios[mapa_data_municipios['NATUREZA'] == crime],
        columns=['NM_MUN_NORM', 'QUANTIDADE'], key_on='feature.properties.NM_MUN_NORM',
        fill_color='YlOrRd', fill_opacity=0.7, line_opacity=0.2,
        legend_name=f'Quantidade de {crime}', show=False, highlight=True
    ).add_to(mapa)

    # Camada de AIS
    folium.Choropleth(
        geo_data=mapa_data_ais[mapa_data_ais['NATUREZA'] == crime],
        name=f"AIS - {crime}", data=mapa_data_ais[mapa_data_ais['NATUREZA'] == crime],
        columns=['nome', 'QUANTIDADE'], key_on='feature.properties.nome',
        fill_color='YlGnBu', fill_opacity=0.7, line_opacity=0.2,
        legend_name=f'Quantidade de {crime}', show=False, highlight=True
    ).add_to(mapa)

folium.LayerControl(collapsed=False).add_to(mapa)

# 5. SALVANDO O MAPA
mapa.save("mapa_interativo_crimes_ce.html")
print("\nSucesso! O arquivo 'mapa_interativo_crimes_ce.html' foi criado.")
