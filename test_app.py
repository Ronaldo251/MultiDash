import pytest
from app import app as flask_app

@pytest.fixture
def app():
    """Cria uma instância da nossa aplicação Flask para ser usada nos testes."""
    yield flask_app

@pytest.fixture
def client(app):
    """Cria um 'cliente' de teste, um navegador simulado para fazer requisições."""
    return app.test_client()


def test_pagina_inicial(client):
    """Testa se a página inicial (/) carrega corretamente."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Dashboard de An\xc3\xa1lise Criminal" in response.data

def test_api_municipios(client):
    """Testa se a API que lista os municípios está funcionando."""
    response = client.get('/api/municipalities')
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) > 180 
    assert 'name' in json_data[0] and 'lat' in json_data[0]

def test_api_year_range(client):
    """NOVO: Testa a API que retorna o intervalo de anos do dataset."""
    response = client.get('/api/year_range')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'min_year' in json_data
    assert 'max_year' in json_data
    assert isinstance(json_data['min_year'], int)
    assert json_data['min_year'] <= json_data['max_year']

def test_api_correlation_data(client):
    """NOVO: Testa a API de correlação com dois crimes válidos."""
    query_params = "crime1=HOMICIDIO DOLOSO&crime2=LATROCINIO"
    response = client.get(f'/api/correlation_data?{query_params}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert isinstance(json_data, list)
    if len(json_data) > 0:
        assert 'x' in json_data[0] and 'y' in json_data[0] and 'year' in json_data[0]

def test_api_correlation_data_parametros_faltando(client):
    """NOVO: Testa se a API de correlação retorna erro 400 se faltar um parâmetro."""
    response = client.get('/api/correlation_data?crime1=HOMICIDIO DOLOSO')
    assert response.status_code == 400

def test_api_mapa_municipios_atualizada(client):
    """ATUALIZADO: Testa a API do mapa de municípios com os novos parâmetros de URL."""
    query_params = "crimes=HOMICIDIO DOLOSO,LATROCINIO&ano_inicio=2018&ano_fim=2020"
    response = client.get(f'/api/municipality_map_data?{query_params}')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'geojson' in json_data
    assert 'max_taxa' in json_data
    assert 'taxa_media_estado' in json_data
    assert 'total_municipios' in json_data

def test_api_mapa_ais_atualizada(client):
    """ATUALIZADO: Testa a API do mapa de AIS com os novos parâmetros de URL."""
    query_params = "crimes=HOMICIDIO DOLOSO&ano_inicio=2019&ano_fim=2021"
    response = client.get(f'/api/ais_map_data?{query_params}')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'geojson' in json_data and 'max_taxa' in json_data

def test_api_mapa_heatmap(client):
    """NOVO: Testa a API do mapa de calor (heatmap)."""
    query_params = "crimes=HOMICIDIO DOLOSO&ano_inicio=2020&ano_fim=2022"
    response = client.get(f'/api/heatmap_map_data?{query_params}')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'points' in json_data
    assert 'max_intensity' in json_data
    assert isinstance(json_data['points'], list)
@pytest.mark.parametrize("endpoint", [
    "/api/data/grafico_evolucao_anual",
    "/api/data/grafico_evolucao_anual_homicidios",
    "/api/data/grafico_comparativo_idade_genero_homicidios",
    "/api/data/grafico_densidade_etaria_homicidios",
    "/api/data/grafico_proporcao_meio_empregado_homicidios",
    "/api/data/grafico_crimes_mulher_dia_hora",
])
def test_apis_de_graficos(client, endpoint):
    """Testa se as APIs de gráficos retornam a estrutura correta."""
    response = client.get(endpoint)
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'labels' in json_data and 'datasets' in json_data

def test_api_evolucao_anual_homicidios_estrutura(client):
    """
    Testa mais a fundo a estrutura da resposta da API de evolução de homicídios,
    verificando se os datasets de Masculino e Feminino estão presentes.
    """
    response = client.get("/api/data/grafico_evolucao_anual_homicidios")
    assert response.status_code == 200
    json_data = response.get_json()
    
    if json_data['datasets']:
        labels = [d['label'] for d in json_data['datasets']]
        assert 'Masculino' in labels
        assert 'Feminino' in labels

