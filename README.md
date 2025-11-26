# Uma Análise Sobre o Aumento da Violência Letal e a Participação Feminina no Crime Organizado Cearense

## 1. Visão Geral do Projeto

Este projeto é um **dashboard de análise de dados full-stack** desenvolvido para investigar a tese de que o aumento da violência letal contra mulheres no Ceará está diretamente ligado à sua crescente e complexa inserção nas dinâmicas do crime organizado.

A aplicação web interativa permite a exploração de um dataset de crimes ocorridos entre 2008 e 2025, oferecendo visualizações geográficas, análises temporais, perfis demográficos e modelagem preditiva para transformar dados brutos em inteligência estratégica.

O objetivo é fornecer uma ferramenta poderosa para gestores públicos, pesquisadores, jornalistas e a sociedade civil, permitindo uma compreensão mais profunda e baseada em evidências sobre a face feminina da criminalidade no estado.

<!-- **[Acesse a Aplicação Web](http://seu-link-aqui.com )** -->

---

## 2. Demonstração Visual

![Demonstração do Dashboard](https://i.imgur.com/ljWmK8U.png )


*prévia da interface principal do dashboard, mostrando o mapa interativo e os gráficos na sidebar.*

---

## 3. Funcionalidades Principais

O dashboard foi construído com uma série de ferramentas interativas que permitem uma análise multidimensional, interativa e profunda dos dados de criminalidade:

-   **🗺️ Mapa Interativo Avançado:**
    -   **Múltiplas Camadas:** Visualização dos dados em três modos distintos:
        -   **Mapa Coroplético (Municípios/AIS):** Análise da taxa de crimes (por 100 mil hab.).
        -   **Mapa de Calor (Heatmap):** Identificação de "hotspots" baseada na densidade de ocorrências.
    -   **Filtros Combinados:** Permite a combinação de múltiplos tipos de crime e a seleção de um **intervalo de anos** específico, recalculando dinamicamente todas as visualizações.
    -   **Interação Multimodo:**
        -   **Seleção Múltipla (Shift+Clique):** Para agregar dados de vários municípios.
        -   **Comparação Direta (Ctrl+Clique):** Para gerar um gráfico comparativo entre dois municípios.
    -   **Busca Inteligente:** Ferramenta de autocomplete para localizar, destacar e aplicar zoom a um município.
    -   **Feedback Visual:** Um **indicador de carregamento** informa o usuário enquanto os dados são processados, e um **tooltip informativo** aparece ao passar o mouse sobre as áreas do mapa.

-   **🔎 Painel de Análise Detalhada (Popup Arrastável):**
    -   Ao selecionar um ou mais municípios, um painel de informações surge com dados contextuais.
    -   **Análise Comparativa (Seleção Única):** Mostra o **Ranking Estadual** da taxa de crime, a **Média do Estado** e a variação percentual do município em relação a ela.
    -   **Tendência Histórica (Seleção Única):** Renderiza um mini-gráfico com a evolução anual dos crimes para o município selecionado.
    -   **Dados Agregados (Seleção Múltipla):** Calcula e exibe a soma de crimes, população total e a taxa de criminalidade para o grupo de municípios selecionados.

-   **📊 Dashboard de Gráficos Dinâmicos:**
    -   **Popups Arrastáveis e Redimensionáveis:** Cada gráfico abre em sua própria janela, permitindo a comparação lado a lado de múltiplas visualizações.
    -   **🔬 Ferramenta de Correlação:** Um gráfico de dispersão (scatter plot) dinâmico que permite ao usuário investigar a correlação anual entre quaisquer dois tipos de crime, ajudando a descobrir relações complexas nos dados.
    -   **Análise de Perfis:** Gráficos detalhados sobre o perfil das vítimas (gênero, idade, raça) e a natureza dos crimes.
    -   **Modelagem Preditiva:** Projeção de tendências futuras (1, 5 ou 10 anos) usando Regressão Linear.

-   **📥 Funcionalidade de Exportação:**
    -   **Exportar Gráfico (PNG):** Salve qualquer visualização de gráfico como uma imagem `.png`.
    -   **Exportar Dados (CSV):** Exporte os dados detalhados da sua seleção no mapa para análise externa.

---

## 4. Arquitetura e Tecnologias Utilizadas

O projeto foi desenvolvido com uma arquitetura full-stack, separando a lógica de backend da interface do usuário.

### Backend
O "cérebro" da aplicação foi construído em **Python** e é responsável por todo o processamento de dados em tempo real, conforme as solicitações do usuário.

-   **Framework Web:** **Flask** foi utilizado para criar o servidor e a API RESTful que entrega os dados processados para o frontend.
-   **Manipulação de Dados:** A biblioteca **Pandas** foi a espinha dorsal para todo o processo de ETL (Extração, Transformação e Carga), incluindo limpeza, filtragem dinâmica por período, agregações complexas e cálculos de correlação entre diferentes variáveis.
-   **Análise Geoespacial:** **GeoPandas** foi essencial para manipular os arquivos `.geojson`, calcular as taxas de criminalidade por área e "dissolver" os polígonos dos municípios para criar a visualização por AIS.
-   **Machine Learning:** **Scikit-learn** foi usado para implementar o modelo de Regressão Linear para a funcionalidade de previsão de tendências.
-   **Cálculos Numéricos:** **NumPy** deu suporte a operações matemáticas, como a transformação de escala (raiz quadrada) para a normalização da intensidade do mapa de calor.


### Frontend
A interface do usuário foi desenvolvida para ser interativa, responsiva e rica em funcionalidades, permitindo a exploração de dados em tempo real.

-   **Estrutura e Estilo:** **HTML5** e **CSS3** (com Flexbox e animações) para a base da aplicação.
-   **Visualização de Mapas:** **Leaflet.js** com o plugin **Leaflet.heat** para criar as camadas interativas, incluindo os mapas de polígonos (choropleth) e o mapa de calor (heatmap).
-   **Visualização de Gráficos:** **Chart.js** com o plugin **Chart.js Datalabels** para renderizar múltiplos tipos de gráficos dinâmicos, incluindo linha, pizza e dispersão (scatter plot).
-   **Interatividade e DOM:** **JavaScript** (ES6+) e **jQuery** para manipulação de eventos, chamadas assíncronas à API (AJAX com `fetch`) e orquestração da interatividade geral.
-   **Componentes de UI Avançados:** **jQuery UI** foi utilizado para implementar o slider de intervalo de anos e as funcionalidades de arrastar (`draggable`) e redimensionar (`resizable`) dos popups.


### Testes
Para garantir a qualidade e a estabilidade do backend, foram criados testes automatizados.

-   **Framework de Teste:** **Pytest** foi utilizado para criar e executar uma suíte de testes que valida todas as rotas da API.

---

## 5. Como Executar o Projeto Localmente

Para executar este projeto em sua máquina local, siga os passos abaixo.

### Pré-requisitos
-   Python 3.8 ou superior
-   pip (gerenciador de pacotes do Python)

### Passos para Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/ronaldo251/nome-do-seu-repositorio.git
    cd nome-do-seu-repositorio
    ```

2.  **Crie e ative um ambiente virtual (recomendado ):**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows (PowerShell)
    .\venv\Scripts\activate

    # Ativar no macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    O arquivo `requirements.txt` contém todas as bibliotecas necessárias.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute a aplicação:**
    ```bash
    python app.py
    ```
    A aplicação estará rodando em `http://127.0.0.1:5000`. Abra este endereço no seu navegador.

5.  **(Opcional ) Execute os testes:**
    Para verificar se todas as rotas da API estão funcionando corretamente:
    ```bash
    pytest
    ```

---

## 6. Desafios e Aprendizados

-   **Qualidade dos Dados e ETL:** O maior desafio inicial foi lidar com os dados brutos, que continham inconsistências, tipos de dados incompatíveis (como `int64` do NumPy vs. JSON) e valores ausentes. O processo de limpeza, conversão de tipos e padronização com Pandas foi fundamental para a viabilidade e estabilidade da API.
-   **Visualização de Dados com Outliers:** A criação do mapa de calor revelou o desafio de visualizar dados com uma distribuição desigual (outliers extremos, como a concentração de crimes em Fortaleza). Foi um aprendizado crucial aplicar uma **transformação de escala (raiz quadrada)** para normalizar a intensidade e gerar uma visualização útil e informativa para todo o estado, em vez de um mapa "achatado" por um único ponto.
-   **Gerenciamento de Estado Complexo no Frontend:** Construir uma interface com múltiplos modos de interação (seleção única, multisseleção com Shift, comparação com Ctrl) sem um framework reativo (como React ou Vue) foi um grande desafio. Exigiu uma estruturação lógica rigorosa e um gerenciamento cuidadoso de eventos e variáveis globais em jQuery para garantir que os diferentes estados não entrassem em conflito.
-   **Performance da API e Otimização de Queries:** Com a adição de filtros dinâmicos (período, tipo de crime), a performance das consultas no `DataFrame` do Pandas se tornou crítica. Foi um exercício prático em otimização, garantindo que a ordem das operações de filtragem e agregação fosse a mais eficiente possível para entregar respostas rápidas ao frontend.
-   **Da Análise ao Insight:** O principal aprendizado foi a jornada de transformar uma simples análise técnica em uma narrativa fundamentada. A criação da ferramenta de correlação, por exemplo, permitiu ir além da visualização de números e começar a investigar e validar hipóteses complexas, como a relação inversa entre a aplicação da Lei Maria da Penha e as taxas de feminicídio.


---

## 7. Autores

**Ronaldo de Oliveira Fraga**

-   **LinkedIn:** [linkedin.com/in/ronaldo-fraga-49a11114a](https://www.linkedin.com/in/ronaldo-fraga-49a11114a/ )
-   **GitHub:** [github.com/ronaldo251](https://github.com/ronaldo251 )
  
**Mirella Camilo Batista da Silva**

-   **LinkedIn:** [linkedin.com/in/mirellacamilo](https://www.linkedin.com/in/mirellacamilo/ )
-   **GitHub:** [github.com/mirellacamilo](https://github.com/mirellacamilo )
