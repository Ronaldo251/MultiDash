// static/js/map.js

document.addEventListener('DOMContentLoaded', function () {
    // =================================================================
    // 1. INICIALIZAÇÃO DO MAPA E VARIÁVEIS GLOBAIS
    // =================================================================
    const map = L.map('map', {
        doubleClickZoom: false // Desativa o zoom padrão do duplo clique
    }).setView([-5.0, -39.5], 7);

    let geojsonLayer = null;
    let highlightLayer = null;
    let lastSelectedLayer = null;

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    } ).addTo(map);

    const crimeSelect = document.getElementById('crime-select');
    const municipioSelect = document.getElementById('municipio-select');

    // =================================================================
    // 2. FUNÇÕES DO MAPA
    // =================================================================

    function getColor(taxa) {
        return taxa > 100 ? '#800026' :
               taxa > 50  ? '#BD0026' :
               taxa > 20  ? '#E31A1C' :
               taxa > 10  ? '#FC4E2A' :
               taxa > 5   ? '#FD8D3C' :
               taxa > 2   ? '#FEB24C' :
               taxa > 0   ? '#FED976' :
                            '#f2f2f2'; // Cor para taxa zero
    }

    function style(feature) {
        return {
            fillColor: getColor(feature.properties.TAXA_POR_100K),
            weight: 1,
            opacity: 1,
            color: 'white',
            dashArray: '3',
            fillOpacity: 0.7
        };
    }

    function highlightFeature(e) {
        const layer = e.target;
        layer.setStyle({
            weight: 3,
            color: '#666',
            dashArray: '',
            fillOpacity: 0.7
        });
        if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
            layer.bringToFront();
        }
    }

    function resetHighlight(e) {
        if (e.target !== lastSelectedLayer) {
            geojsonLayer.resetStyle(e.target);
        }
    }

    function zoomToFeature(e) {
        const layer = e.target;
        
        // Remove destaque antigo
        if (lastSelectedLayer) {
            geojsonLayer.resetStyle(lastSelectedLayer);
        }
        
        // Aplica novo destaque
        layer.setStyle({
            weight: 4,
            color: '#0000FF',
            fillOpacity: 0.2
        });
        lastSelectedLayer = layer;
        
        // Centraliza no município
        map.fitBounds(layer.getBounds());
    }

    async function carregarDadosNoMapa(crime) {
        try {
            const response = await fetch(`/api/dados_mapa?crime=${encodeURIComponent(crime)}`);
            const geojsonDataString = await response.json();
            const geojsonData = JSON.parse(geojsonDataString);

            if (geojsonLayer) {
                map.removeLayer(geojsonLayer);
            }

            geojsonLayer = L.geoJSON(geojsonData, {
                style: style,
                onEachFeature: (feature, layer) => {
                    const props = feature.properties;
                    const popupContent = `
                        <b>Município:</b> ${props.name}  

                        <b>Nº Absoluto:</b> ${props.QUANTIDADE}  

                        <b>Taxa/100k Hab:</b> ${props.TAXA_POR_100K.toFixed(2)}
                    `;
                    layer.bindTooltip(popupContent);
                    layer.on({
                        mouseover: highlightFeature,
                        mouseout: resetHighlight,
                        click: zoomToFeature
                    });
                }
            }).addTo(map);
        } catch (error) {
            console.error("Falha ao carregar dados do mapa:", error);
        }
    }

    // =================================================================
    // 3. CONTROLES E EVENTOS
    // =================================================================

    fetch('/api/municipios')
        .then(response => response.json())
        .then(municipios => {
            const defaultOption = document.createElement('option');
            defaultOption.value = "Estado Completo";
            defaultOption.textContent = "Ver Estado Completo";
            municipioSelect.appendChild(defaultOption);
            municipios.forEach(municipio => {
                const option = document.createElement('option');
                option.value = municipio;
                option.textContent = municipio;
                municipioSelect.appendChild(option);
            });
        });

    crimeSelect.addEventListener('change', () => carregarDadosNoMapa(crimeSelect.value));

    municipioSelect.addEventListener('change', () => {
        const municipioNome = municipioSelect.value;
        if (municipioNome === "Estado Completo") {
            map.setView([-5.0, -39.5], 7);
            if (lastSelectedLayer) {
                geojsonLayer.resetStyle(lastSelectedLayer);
                lastSelectedLayer = null;
            }
        } else {
            geojsonLayer.eachLayer(layer => {
                if (layer.feature.properties.name === municipioNome) {
                    layer.fire('click');
                }
            });
        }
    });

    // Lógica de duplo clique para alternar zoom
    let zoomToggle = true;
    map.on('dblclick', function() {
        if (zoomToggle) {
            map.zoomIn();
        } else {
            map.zoomOut();
        }
        zoomToggle = !zoomToggle;
    });

    // Remove destaque ao clicar fora de um município
    map.on('click', function() {
        if (lastSelectedLayer) {
            geojsonLayer.resetStyle(lastSelectedLayer);
            lastSelectedLayer = null;
        }
    });

    // Carga inicial
    carregarDadosNoMapa(crimeSelect.value);
});
