// Inicializa o mapa
const map = L.map('map').setView([-5.0, -39.5], 7);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
} ).addTo(map);

// Função para buscar os dados da nossa API Flask e desenhar no mapa
async function carregarDadosNoMapa(crime) {
    const response = await fetch(`/api/dados_mapa?crime=${crime}`);
    const geojsonData = await response.json();
    const data = JSON.parse(geojsonData);

    // Aqui você adicionaria a camada Choropleth (cores)
    // E adicionaria os eventos de clique e duplo clique
    L.geoJSON(data, {
        onEachFeature: function (feature, layer) {
            // Destaque ao passar o mouse
            layer.on('mouseover', function (e) {
                this.setStyle({ weight: 3, color: '#666' });
            });
            layer.on('mouseout', function (e) {
                // Reseta o estilo
            });

            // Lógica de clique para destacar
            layer.on('click', function (e) {
                // Lógica para destacar permanentemente (ou até outro clique)
            });
        }
    }).addTo(map);
}

// Lógica para o duplo clique (zoom in/out)
let zoomToggle = true;
map.on('dblclick', function() {
    if (zoomToggle) {
        map.zoomIn();
    } else {
        map.zoomOut();
    }
    zoomToggle = !zoomToggle;
});


// Carrega os dados iniciais
carregarDadosNoMapa('HOMICIDIO DOLOSO');
