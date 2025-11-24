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

O dashboard foi construído com uma série de funcionalidades para permitir uma análise multidimensional e interativa:

-   **🗺️ Mapa Coroplético Avançado:**
    -   Visualização da taxa de crimes (por 100 mil hab.) em duas granularidades: **Municípios** e **Áreas Integradas de Segurança (AIS)**.
    -   **Seleção Múltipla de Crimes:** Permite a combinação de diferentes tipos de crime para uma análise agregada no mapa.
    -   **Interação com Shift + Clique:** Selecione múltiplos municípios para análises comparativas e agregadas.
    -   **Busca Inteligente:** Ferramenta de autocomplete para localizar, destacar e aplicar zoom a um município específico.
    -   **Indicador de Carregamento:** Um *spinner* de carregamento fornece feedback visual ao usuário enquanto os dados geográficos são processados.

-   **🔎 Painel de Análise Detalhada (Popup Arrastável):**
    -   Ao selecionar um ou mais municípios, um painel de informações surge com dados contextuais.
    -   **Análise Comparativa (Seleção Única):** Mostra o **Ranking Estadual** da taxa de crime, a **Média do Estado** e a variação percentual do município em relação a ela.
    -   **Tendência Histórica (Seleção Única):** Renderiza um mini-gráfico com a evolução anual dos crimes para o município selecionado.
    -   **Dados Agregados (Seleção Múltipla):** Calcula e exibe a soma de crimes, população total e a taxa de criminalidade para o grupo de municípios selecionados.

-   **📊 Dashboard de Gráficos Interativos:**
    -   **Popups Arrastáveis e Redimensionáveis:** Cada gráfico abre em sua própria janela, permitindo a comparação lado a lado de múltiplas visualizações.
    -   **Análise Comparativa de Gênero:** Gráficos que contrastam a vitimização e o perfil etário entre homens e mulheres.
    -   **Análise Focada na Mulher:** Seção dedicada a explorar as particularidades dos crimes contra mulheres (dinâmica temporal, meio empregado, etc.).
    -   **Modelagem Preditiva:** Projeção de tendências futuras (1, 5 ou 10 anos) usando Regressão Linear.

-   **📥 Funcionalidade de Exportação:**
    -   **Exportar Gráfico (PNG):** Cada gráfico pode ser salvo como uma imagem `.png` com um único clique.
    -   **Exportar Dados (CSV):** Os dados detalhados da seleção de municípios no mapa podem ser exportados para um arquivo `.csv` para análise externa.


---

## 4. Arquitetura e Tecnologias Utilizadas

O projeto foi desenvolvido com uma arquitetura full-stack, separando a lógica de backend da interface do usuário.

### Backend
O "cérebro" da aplicação foi construído em **Python** e é responsável por todo o processamento de dados.

-   **Framework Web:** **Flask** foi utilizado para criar o servidor e a API RESTful que entrega os dados processados para o frontend.
-   **Manipulação de Dados:** A biblioteca **Pandas** foi a espinha dorsal para todo o processo de ETL (Extração, Transformação e Carga), incluindo limpeza, filtragem e agregação dos dados.
-   **Análise Geoespacial:** **GeoPandas** foi essencial para manipular os arquivos `.geojson`, calcular as taxas de criminalidade por área e "dissolver" os polígonos dos municípios para criar a visualização por AIS.
-   **Machine Learning:** **Scikit-learn** foi usado para implementar o modelo de Regressão Linear para a funcionalidade de previsão de tendências.
-   **Cálculos Numéricos:** **NumPy** deu suporte a operações matemáticas e à criação de arrays para a modelagem preditiva.

### Frontend
A interface do usuário foi desenvolvida para ser interativa, responsiva e rica em funcionalidades.

-   **Estrutura e Estilo:** **HTML5** e **CSS3** para a base da aplicação.
-   **Visualização de Mapas:** **Leaflet.js** para a renderização dos mapas coropléticos e interações geográficas.
-   **Visualização de Gráficos:** **Chart.js** com o plugin **Chart.js Datalabels** para criar gráficos dinâmicos e informativos.
-   **Interatividade e DOM:** **JavaScript** puro e **jQuery** para manipulação de eventos, chamadas de API (AJAX) e interatividade geral.
-   **Componentes de UI Avançados:** **jQuery UI** foi utilizado para implementar as funcionalidades de arrastar (`draggable`) e redimensionar (`resizable`) dos popups.


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

-   **Qualidade dos Dados:** O maior desafio inicial foi lidar com os dados brutos, que continham inconsistências e valores ausentes. O processo de limpeza e padronização com Pandas foi fundamental para a viabilidade do projeto.
-   **Performance Geoespacial:** O cálculo de centroides e a dissolução de polígonos com GeoPandas são operações computacionalmente intensivas. Foi um grande aprendizado otimizar esses processos para que o carregamento inicial da aplicação fosse rápido.
-   **Lógica de Frontend:** Integrar múltiplas bibliotecas JavaScript (Leaflet, Chart.js, jQuery) e garantir que os filtros e pop-ups funcionassem em harmonia exigiu uma estruturação cuidadosa do código.
-   **Da Análise ao Insight:** O principal aprendizado foi a jornada de transformar uma simples análise técnica em uma narrativa fundamentada, conectando os padrões encontrados nos dados com a teoria acadêmica sobre criminologia.
-   **Gerenciamento de Estado no Frontend:** Construir uma interface com múltiplos estados (seleção única, multisseleção, popups abertos, filtros ativos) sem um framework de frontend moderno (como React ou Vue) foi um desafio. Exigiu um gerenciamento cuidadoso de variáveis globais e eventos em jQuery para garantir que a interface se comportasse de forma consistente e sem bugs.

---

## 7. Autores

**Ronaldo de Oliveira Fraga**

-   **LinkedIn:** [linkedin.com/in/ronaldo-fraga-49a11114a](https://www.linkedin.com/in/ronaldo-fraga-49a11114a/ )
-   **GitHub:** [github.com/ronaldo251](https://github.com/ronaldo251 )
  
**Mirella Camilo Batista da Silva**

-   **LinkedIn:** [linkedin.com/in/mirellacamilo](https://www.linkedin.com/in/mirellacamilo/ )
-   **GitHub:** [github.com/mirellacamilo](https://github.com/mirellacamilo )
