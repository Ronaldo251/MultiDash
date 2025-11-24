
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

def test_api_mapa_municipios(client):
    """Testa a API do mapa de municípios para um crime específico."""
    response = client.get('/api/municipality_map_data/HOMICIDIO DOLOSO')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'geojson' in json_data and 'max_taxa' in json_data

def test_api_mapa_ais(client):
    """Testa a API do mapa de AIS para um crime específico."""
    response = client.get('/api/ais_map_data/HOMICIDIO DOLOSO')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'geojson' in json_data and 'max_taxa' in json_data

@pytest.mark.parametrize("endpoint", [

    "/api/data/grafico_evolucao_anual",
    "/api/data/grafico_evolucao_anual_homicidios",
    "/api/data/grafico_comparativo_idade_genero_homicidios",

    "/api/data/grafico_densidade_etaria_homicidios",
    "/api/data/grafico_proporcao_meio_empregado_homicidios",
    "/api/data/grafico_crimes_mulher_dia_hora",
])
def test_novas_apis_de_graficos(client, endpoint):
    """Testa todas as APIs de gráficos da nova estrutura focada."""
    response_geral = client.get(endpoint)
    assert response_geral.status_code == 200
    json_data_geral = response_geral.get_json()
    assert 'labels' in json_data_geral and 'datasets' in json_data_geral

    response_fem = client.get(f"{endpoint}?genero=feminino")
    assert response_fem.status_code == 200
    json_data_fem = response_fem.get_json()
    assert 'labels' in json_data_fem and 'datasets' in json_data_fem

# --- T(ROTAS ANTIGAS) ---

# - /api/data/grafico_distribuicao_raca
# - /api/data/grafico_comparativo_crime_log
# - /api/data/grafico_proporcao_genero_crime
# - /api/data/grafico_evolucao_odio
# - etc.

def test_api_evolucao_anual_homicidios_estrutura(client):
    """
    Testa mais a fundo a estrutura da resposta da API de evolução de homicídios,
    verificando se os datasets de Masculino e Feminino estão presentes.
    """
    response = client.get("/api/data/grafico_evolucao_anual_homicidios")
    assert response.status_code == 200
    json_data = response.get_json()
    
    labels = [d['label'] for d in json_data['datasets']]
    assert 'Masculino' in labels
    assert 'Feminino' in labels
