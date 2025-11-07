# app.py (Versão com APIs para Gráficos 6a e 6b)

import pandas as pd
import geopandas as gpd
from flask import Flask, jsonify, render_template, request # Adiciona 'request'
import json

app = Flask(__name__)

# --- CARREGAMENTO E PROCESSAMENTO (sem alterações) ---
print("Iniciando o carregamento e processamento dos dados...")
try:
    df_crimes = pd.read_csv('crimes.csv', sep=',')
    gdf_municipios = gpd.read_file('municipios_ce.geojson')
    df_populacao = pd.read_csv('populacao_ce.csv')
    df_crimes.columns = ['AIS', 'NATUREZA', 'MUNICIPIO', 'LOCAL', 'DATA', 'HORA', 'DIA_SEMANA','MEIO_EMPREGADO', 'GENERO', 'ORIENTACAO_SEXUAL', 'IDADE_VITIMA','ESCOLARIDADE_VITIMA', 'RACA_VITIMA']
except FileNotFoundError as e:
    print(f"ERRO CRÍTICO: Arquivo não encontrado - {e}.")
    exit()

def normalize_text(text_series):
    return text_series.str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

df_crimes['MUNICIPIO_NORM'] = normalize_text(df_crimes['MUNICIPIO'])
gdf_municipios['NM_MUN_NORM'] = normalize_text(gdf_municipios['name'])
df_populacao['MUNICIPIO_NORM'] = normalize_text(df_populacao['municipio'])
crimes_agrupados = df_crimes.groupby(['MUNICIPIO_NORM', 'NATUREZA']).size().reset_index(name='QUANTIDADE')
crimes_com_pop = pd.merge(crimes_agrupados, df_populacao[['MUNICIPIO_NORM', 'populacao']], on='MUNICIPIO_NORM', how='left')
crimes_com_pop.dropna(subset=['populacao'], inplace=True)
crimes_com_pop['TAXA_POR_100K'] = (crimes_com_pop['QUANTIDADE'] / crimes_com_pop['populacao']) * 100000
LISTA_DE_CRIMES = sorted(df_crimes['NATUREZA'].dropna().unique().tolist())
df_crimes['DATA'] = pd.to_datetime(df_crimes['DATA'], dayfirst=True, errors='coerce')
df_crimes['ANO'] = df_crimes['DATA'].dt.year
mapeamento_genero = {'Masculino': 'Masculino', 'Homem Trans': 'Masculino', 'Feminino': 'Feminino', 'Mulher Trans': 'Feminino', 'Travesti': 'Feminino'}
df_crimes['GENERO_AGRUPADO'] = df_crimes['GENERO'].map(mapeamento_genero)
print("Processamento de dados concluído. Aplicação pronta.")
# --- FIM DO PROCESSAMENTO ---

@app.route('/')
def index():
    return render_template('index.html', crimes=LISTA_DE_CRIMES)

# --- ROTAS DE API EXISTENTES (sem alterações, omitidas para brevidade) ---
@app.route('/api/map_data/<crime_type>')
def get_map_data(crime_type):
    dados_do_crime = crimes_com_pop[crimes_com_pop['NATUREZA'] == crime_type]
    mapa_completo = gdf_municipios.merge(dados_do_crime[['MUNICIPIO_NORM', 'QUANTIDADE', 'TAXA_POR_100K']], left_on='NM_MUN_NORM', right_on='MUNICIPIO_NORM', how='left')
    mapa_completo[['QUANTIDADE', 'TAXA_POR_100K']] = mapa_completo[['QUANTIDADE', 'TAXA_POR_100K']].fillna(0)
    max_taxa = mapa_completo['TAXA_POR_100K'].max()
    return jsonify({'geojson': json.loads(mapa_completo.to_json()), 'max_taxa': max_taxa})

@app.route('/api/data/grafico_evolucao_anual')
def get_data_grafico_evolucao_anual():
    df_analise = df_crimes.dropna(subset=['ANO', 'GENERO_AGRUPADO'])
    df_analise['ANO'] = df_analise['ANO'].astype(int)
    dados_grafico = df_analise.groupby(['ANO', 'GENERO_AGRUPADO']).size().reset_index(name='TOTAL')
    dados_pivot = dados_grafico.pivot(index='ANO', columns='GENERO_AGRUPADO', values='TOTAL').fillna(0)
    return jsonify({'labels': dados_pivot.index.tolist(), 'datasets': [{'label': 'Masculino', 'data': dados_pivot['Masculino'].tolist(), 'borderColor': 'rgba(54, 162, 235, 1)', 'backgroundColor': 'rgba(54, 162, 235, 0.5)'}, {'label': 'Feminino', 'data': dados_pivot['Feminino'].tolist(), 'borderColor': 'rgba(255, 99, 132, 1)', 'backgroundColor': 'rgba(255, 99, 132, 0.5)'}]})

@app.route('/api/data/grafico_crimes_mulher_dia_hora')
def get_data_grafico_crimes_mulher_dia_hora():
    df_feminino = df_crimes[df_crimes['GENERO_AGRUPADO'] == 'Feminino'].copy()
    if df_feminino.empty: return jsonify({'labels': [], 'datasets': []})
    df_feminino['HORA_NUM'] = pd.to_datetime(df_feminino['HORA'], format='%H:%M:%S', errors='coerce').dt.hour
    df_feminino.dropna(subset=['HORA_NUM'], inplace=True)
    df_feminino['HORA_NUM'] = df_feminino['HORA_NUM'].astype(int)
    ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    df_feminino['DIA_SEMANA'] = pd.Categorical(df_feminino['DIA_SEMANA'], categories=ordem_dias, ordered=True)
    crimes_por_dia_hora = df_feminino.groupby(['DIA_SEMANA', 'HORA_NUM']).size().unstack(fill_value=0)
    datasets = []
    cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF']
    for i, dia in enumerate(ordem_dias):
        if dia in crimes_por_dia_hora.index:
            datasets.append({'label': dia, 'data': crimes_por_dia_hora.loc[dia].reindex(range(24), fill_value=0).tolist(), 'borderColor': cores[i], 'backgroundColor': cores[i], 'fill': False, 'tension': 0.1})
    return jsonify({'labels': list(range(24)), 'datasets': datasets})

@app.route('/api/data/grafico_comparativo_crime_log')
def get_data_grafico_3a():
    df_analise = df_crimes.dropna(subset=['GENERO_AGRUPADO', 'NATUREZA'])
    crimes_por_natureza = df_analise.groupby(['NATUREZA', 'GENERO_AGRUPADO']).size().unstack(fill_value=0)
    crimes_por_natureza['TOTAL'] = crimes_por_natureza.sum(axis=1)
    crimes_por_natureza = crimes_por_natureza.sort_values('TOTAL', ascending=False)
    return jsonify({'labels': crimes_por_natureza.index.tolist(), 'datasets': [{'label': 'Masculino', 'data': crimes_por_natureza['Masculino'].tolist(), 'backgroundColor': 'rgba(54, 162, 235, 0.7)'}, {'label': 'Feminino', 'data': crimes_por_natureza['Feminino'].tolist(), 'backgroundColor': 'rgba(255, 99, 132, 0.7)'}]})

@app.route('/api/data/grafico_proporcao_genero_crime')
def get_data_grafico_3b():
    df_analise = df_crimes.dropna(subset=['GENERO_AGRUPADO', 'NATUREZA'])
    crimes_por_natureza = df_analise.groupby(['NATUREZA', 'GENERO_AGRUPADO']).size().reset_index(name='QUANTIDADE')
    total_por_natureza = crimes_por_natureza.groupby('NATUREZA')['QUANTIDADE'].transform('sum')
    crimes_por_natureza['PROPORCAO_%'] = (crimes_por_natureza['QUANTIDADE'] / total_por_natureza) * 100
    df_pivot = crimes_por_natureza.pivot(index='NATUREZA', columns='GENERO_AGRUPADO', values='PROPORCAO_%').fillna(0)
    df_pivot = df_pivot.sort_values('Feminino', ascending=True)
    return jsonify({'labels': df_pivot.index.tolist(), 'datasets': [{'label': 'Masculino', 'data': df_pivot['Masculino'].tolist(), 'backgroundColor': 'rgba(54, 162, 235, 0.7)'}, {'label': 'Feminino', 'data': df_pivot['Feminino'].tolist(), 'backgroundColor': 'rgba(255, 99, 132, 0.7)'}]})

@app.route('/api/data/grafico_distribuicao_raca')
def get_data_grafico_4():
    df_raca = df_crimes[df_crimes['RACA_VITIMA'] != 'NÃO INFORMADA'].copy()
    if df_raca.empty: return jsonify({'labels': [], 'datasets': []})
    contagem_raca = df_raca['RACA_VITIMA'].value_counts()
    return jsonify({'labels': contagem_raca.index.tolist(), 'datasets': [{'label': 'Total de Vítimas', 'data': contagem_raca.values.tolist(), 'backgroundColor': ['#440154', '#482878', '#3e4a89', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6dcd59', '#b4de2c', '#fde725']}]})

def get_clean_age_df():
    df_idade = df_crimes.copy()
    df_idade['IDADE_NUM'] = pd.to_numeric(df_idade['IDADE_VITIMA'], errors='coerce')
    df_idade.dropna(subset=['IDADE_NUM', 'GENERO_AGRUPADO'], inplace=True)
    df_idade['IDADE_NUM'] = df_idade['IDADE_NUM'].astype(int)
    df_idade = df_idade[(df_idade['IDADE_NUM'] >= 0) & (df_idade['IDADE_NUM'] <= 110)]
    return df_idade

@app.route('/api/data/grafico_distribuicao_etaria')
def get_data_grafico_5a():
    df_idade = get_clean_age_df()
    if df_idade.empty: return jsonify({'labels': [], 'datasets': []})
    bins = range(0, 111, 10)
    labels = [f'{i}-{i+9}' for i in bins[:-1]]
    df_idade['FAIXA_ETARIA'] = pd.cut(df_idade['IDADE_NUM'], bins=bins, labels=labels, right=False)
    contagem_faixa = df_idade['FAIXA_ETARIA'].value_counts().sort_index()
    return jsonify({'labels': contagem_faixa.index.tolist(), 'datasets': [{'label': 'Número de Vítimas', 'data': contagem_faixa.values.tolist(), 'backgroundColor': 'rgba(75, 192, 192, 0.7)'}]})

@app.route('/api/data/grafico_comparativo_idade_genero')
def get_data_grafico_5b():
    df_idade = get_clean_age_df()
    if df_idade.empty: return jsonify({'labels': [], 'datasets': []})
    dados_grafico = df_idade.groupby(['IDADE_NUM', 'GENERO_AGRUPADO']).size().unstack(fill_value=0)
    if 'Masculino' not in dados_grafico: dados_grafico['Masculino'] = 0
    if 'Feminino' not in dados_grafico: dados_grafico['Feminino'] = 0
    dados_grafico = dados_grafico.reindex(range(111), fill_value=0)
    return jsonify({'labels': dados_grafico.index.tolist(), 'datasets': [{'label': 'Masculino', 'data': dados_grafico['Masculino'].tolist(), 'borderColor': 'rgba(54, 162, 235, 1)', 'backgroundColor': 'rgba(54, 162, 235, 0.5)', 'fill': False, 'tension': 0.2}, {'label': 'Feminino', 'data': dados_grafico['Feminino'].tolist(), 'borderColor': 'rgba(255, 99, 132, 1)', 'backgroundColor': 'rgba(255, 99, 132, 0.5)', 'fill': False, 'tension': 0.2}]})

# --- NOVAS ROTAS DE API PARA OS GRÁFICOS 6a e 6b ---

def get_meio_empregado_df(filtro_genero='todos'):
    """Função auxiliar para filtrar e limpar dados de Meio Empregado."""
    df_filtrado = df_crimes.copy()
    if filtro_genero == 'feminino':
        df_filtrado = df_crimes[df_crimes['GENERO_AGRUPADO'] == 'Feminino'].copy()
    
    df_meio = df_filtrado.dropna(subset=['MEIO_EMPREGADO'])
    df_meio = df_meio[df_meio['MEIO_EMPREGADO'] != 'NÃO INFORMADO'].copy()
    return df_meio

@app.route('/api/data/grafico_proporcao_meio_empregado')
def get_data_grafico_6a():
    """ Prepara dados para o Gráfico 6a: Proporção do Meio Empregado (Pizza). """
    filtro = request.args.get('filtro', 'todos') # Pega o parâmetro 'filtro' da URL
    df_meio = get_meio_empregado_df(filtro)
    
    if df_meio.empty: return jsonify({'labels': [], 'datasets': []})
        
    contagem_meio = df_meio['MEIO_EMPREGADO'].value_counts()
    
    output = {
        'labels': contagem_meio.index.tolist(),
        'datasets': [{
            'label': 'Meio Empregado',
            'data': contagem_meio.values.tolist(),
            'backgroundColor': ['#440154', '#482878', '#3e4a89', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6dcd59', '#b4de2c', '#fde725']
        }]
    }
    return jsonify(output)

@app.route('/api/data/grafico_evolucao_meio_empregado')
def get_data_grafico_6b():
    """ Prepara dados para o Gráfico 6b: Evolução do Meio Empregado (Linhas). """
    filtro = request.args.get('filtro', 'todos')
    df_meio = get_meio_empregado_df(filtro)
    
    if df_meio.empty: return jsonify({'labels': [], 'datasets': []})
    
    df_meio = df_meio.dropna(subset=['ANO'])
    df_meio['ANO'] = df_meio['ANO'].astype(int)
    
    evolucao_meio = df_meio.groupby(['ANO', 'MEIO_EMPREGADO']).size().unstack(fill_value=0)
    
    datasets = []
    cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#440154', '#21908d', '#fde725']
    
    for i, meio in enumerate(evolucao_meio.columns):
        datasets.append({
            'label': meio,
            'data': evolucao_meio[meio].tolist(),
            'borderColor': cores[i % len(cores)],
            'fill': False,
            'tension': 0.1
        })
        
    output = {
        'labels': evolucao_meio.index.tolist(),
        'datasets': datasets
    }
    return jsonify(output)


if __name__ == '__main__':
    app.run(debug=True)
