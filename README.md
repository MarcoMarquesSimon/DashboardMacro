# Dashboard de Precos dos Titulos Publicos

## Visao geral

Este projeto consiste em um webapp desenvolvido em Streamlit para visualizacao interativa dos precos e taxas dos titulos publicos do Tesouro Direto. O objetivo do aplicativo e oferecer uma interface limpa, profissional e orientada a analise, permitindo filtrar os dados por tipo de titulo, intervalo de datas e vencimentos, alem de acompanhar a evolucao historica de metricas relevantes.

A aplicacao foi desenhada para priorizar:

- clareza visual;
- desempenho no carregamento;
- leitura financeira objetiva;
- facilidade de manutencao e extensao.

O dashboard utiliza dados publicos disponibilizados pelo Tesouro Transparente, lidos diretamente a partir de um arquivo CSV hospedado na infraestrutura oficial do governo.

## Principais funcionalidades

### 1. Carregamento automatico da base

O app consome automaticamente o dataset de precos e taxas do Tesouro Direto, sem necessidade de download manual do usuario.

### 2. Filtros interativos

O painel principal permite:

- selecionar um ou mais tipos de titulo;
- definir intervalo de datas por calendario;
- escolher a metrica principal exibida no grafico;
- refinar os vencimentos exibidos.

Por padrao, o filtro de vencimentos prioriza apenas titulos ainda vigentes. Titulos com vencimento passado podem ser incluidos opcionalmente.

### 3. Separacao correta por titulo e vencimento

Cada serie exibida no grafico representa a combinacao:

- tipo de titulo;
- data de vencimento.

Isso evita agregacoes indevidas entre vencimentos diferentes de um mesmo titulo.

### 4. Grafico principal de evolucao temporal

O grafico central mostra a evolucao historica da metrica selecionada ao longo da Data Base, com uma serie separada para cada combinacao de titulo e vencimento.

O grafico tambem destaca:

- valor atual;
- valor minimo;
- valor maximo.

Quando existem muitas series, o app reduz a quantidade de marcacoes visuais para preservar a limpeza do layout.

### 5. Painel lateral de indicadores

Ao lado do grafico principal, o app exibe indicadores resumidos com leitura rapida:

- taxa media;
- PU medio;
- valor atual;
- valor minimo;
- valor maximo.

### 6. Tabela detalhada

O usuario pode consultar a base filtrada em formato tabular, com:

- colunas principais exibidas por padrao;
- colunas adicionais opcionais;
- exportacao dos dados filtrados em CSV.

### 7. Estrutura preparada para expansao

A sidebar foi mantida como area de navegacao. Alem do dashboard principal de Tesouro Direto, o projeto ja inclui uma pagina reservada para um futuro painel de analise macro.

## Arquitetura do projeto

A estrutura minima esperada do projeto e a seguinte:

```text
projeto_tesouro/
├── app.py
├── dados_tesouro.py
└── README_webapp_tesouro_direto.md
```

### `app.py`

Arquivo principal da aplicacao Streamlit. Responsavel por:

- configuracao da pagina;
- aplicacao do tema visual;
- renderizacao dos filtros;
- construcao dos graficos;
- exibicao das KPIs;
- renderizacao da tabela;
- navegacao entre paineis.

### `dados_tesouro.py`

Modulo responsavel pela carga e padronizacao da base. Contem a funcao que:

- le o CSV do Tesouro;
- converte colunas de data;
- converte colunas numericas;
- devolve um DataFrame pronto para uso.

## Dataset utilizado

O aplicativo usa o arquivo CSV oficial do Tesouro Transparente referente aos precos e taxas dos titulos do Tesouro Direto.

### Colunas principais da base

A base carregada possui, atualmente, as seguintes colunas:

- `Tipo Titulo`
- `Data Vencimento`
- `Data Base`
- `Taxa Compra Manha`
- `Taxa Venda Manha`
- `PU Compra Manha`
- `PU Venda Manha`
- `PU Base Manha`

### Interpretacao geral das colunas

- **Tipo Titulo**: nome do titulo publico.
- **Data Vencimento**: data de vencimento do papel.
- **Data Base**: data de referencia do preco/taxa.
- **Taxa Compra Manha**: taxa praticada na compra no periodo da manha.
- **Taxa Venda Manha**: taxa praticada na venda no periodo da manha.
- **PU Compra Manha**: preco unitario de compra no periodo da manha.
- **PU Venda Manha**: preco unitario de venda no periodo da manha.
- **PU Base Manha**: preco unitario de referencia no periodo da manha.

## Requisitos

Para executar o projeto, e recomendavel usar Python 3.10 ou superior.

### Bibliotecas necessarias

- `streamlit`
- `pandas`
- `plotly`

Instalacao via `pip`:

```bash
pip install streamlit pandas plotly
```

## Como executar o projeto

No terminal, dentro da pasta do projeto, execute:

```bash
streamlit run app.py
```

O Streamlit iniciara um servidor local e abrira o aplicativo no navegador.

## Funcao de carga de dados

O modulo `dados_tesouro.py` deve conter uma funcao semelhante a esta:

```python
import pandas as pd


def dados_tesouro(url):
    df = pd.read_csv(url, sep=';')

    df['Data Vencimento'] = pd.to_datetime(df['Data Vencimento'], format='%d/%m/%Y')
    df['Data Base'] = pd.to_datetime(df['Data Base'], format='%d/%m/%Y')

    for coluna in df.columns[3:]:
        df[coluna] = df[coluna].replace(',', '.', regex=True)
        df[coluna] = df[coluna].astype(float)

    return df
```

## Logica de funcionamento

### 1. Carga e cache

Ao iniciar, o app carrega os dados a partir da URL oficial e utiliza cache para evitar recargas desnecessarias a cada interacao. Isso melhora significativamente o desempenho.

### 2. Filtragem principal

Os filtros de topo atuam sobre:

- tipos de titulo;
- intervalo da Data Base;
- metrica principal do grafico.

### 3. Refinamento por vencimento

O filtro de vencimentos aparece em um bloco secundario, mais discreto. Essa escolha foi feita para manter o layout limpo.

A logica aplicada e:

- selecionar automaticamente apenas vencimentos futuros ou vigentes;
- permitir a inclusao manual de vencimentos passados;
- manter cada vencimento como serie independente.

### 4. Construcao do identificador de serie

Cada linha e identificada por um nome de serie padronizado:

```text
Tipo Titulo • Data Vencimento
```

Isso garante clareza na legenda e nos marcadores do grafico.

### 5. Painel de indicadores

As KPIs laterais resumem a condicao atual do recorte selecionado, oferecendo leitura rapida sem competir visualmente com o grafico principal.

### 6. Tabela e exportacao

A tabela final permite inspecao detalhada e exportacao da base filtrada para CSV, facilitando analises externas.

## Identidade visual

O webapp foi construindo com uma paleta institucional, priorizando contraste, legibilidade e sobriedade.

### Paleta principal

- Azul principal: `#0F46AB`
- Azul escuro de fundo: `#061630`
- Texto claro: `#E6E6E6`
- Superficie secundaria: `#2B2B2B`

### Objetivos visuais

- manter a interface limpa;
- reduzir excesso de elementos simultaneos;
- destacar o grafico principal como foco da analise;
- usar indicadores compactos e discretos;
- transmitir uma estetica proxima a dashboards institucionais e financeiros.

## Decisoes de design

Algumas decisoes importantes no projeto:

### Sidebar reservada para navegacao

A sidebar nao concentra filtros. Ela foi mantida apenas para alternar entre dashboards, evitando poluicao visual na lateral.

### Filtros em barra superior

Os filtros principais foram colocados no topo, em formato horizontal, para facilitar leitura e reduzir a sensacao de formulario extenso.

### KPIs compactas

As KPIs ficam em uma coluna lateral, com cards curtos e de fundo solido, servindo como apoio de leitura e nao como elemento central.

### Grafico como foco principal

O layout favorece a largura do grafico de evolucao temporal, uma vez que ele representa o elemento mais importante para a interpretacao dos dados.

### Tabela simplificada por padrao

Para manter a interface limpa, a tabela detalhada exibe inicialmente apenas as colunas mais relevantes. Colunas complementares ficam disponiveis sob demanda.

## Personalizacao e manutencao

O projeto foi estruturado para facilitar evolucoes futuras.

### Alterar a fonte dos dados

Para trocar o dataset, basta substituir a URL utilizada no `app.py` e garantir que a estrutura das colunas seja compatível com o parser.

### Alterar a paleta

As cores principais estao centralizadas em variaveis no topo do `app.py`, o que facilita ajustes de identidade visual.

### Adicionar novas metricas

Novas colunas numericas podem ser incorporadas ao seletor de metricas desde que existam na base e sejam tratadas na carga.

### Criar novos dashboards

A pagina de analise macro ja esta prevista e pode ser expandida com novos datasets, indicadores e graficos sem alterar a estrutura principal do app.

## Possiveis melhorias futuras

Algumas evolucoes recomendadas para as proximas versoes:

- renomear as metricas com rotulos mais amigaveis na interface;
- incluir comparacao entre dois titulos especificos;
- adicionar variacao diaria, semanal ou acumulada;
- criar filtros avancados por faixa de taxa ou faixa de PU;
- adicionar tabela com ranking de titulos;
- incluir exportacao em Excel;
- integrar indicadores macroeconomicos no segundo painel;
- adicionar documentacao tecnica de deploy.

## Boas praticas recomendadas

Para manter o projeto robusto e organizado:

- manter o parser de dados separado da interface;
- evitar logica de transformacao diretamente no layout quando possivel;
- validar a estrutura da base sempre que o dataset oficial mudar;
- testar o app com multiplas combinacoes de filtros;
- revisar o layout ao adicionar novos componentes para nao comprometer a limpeza visual.

## Solucao de problemas

### O app nao inicia

Verifique se as bibliotecas necessarias estao instaladas corretamente e se o comando esta sendo executado na pasta do projeto.

### O dataset nao carrega

Verifique:

- conexao com a internet;
- disponibilidade da URL oficial;
- possiveis mudancas no layout do CSV publicado.

### O grafico aparece vazio

Isso geralmente ocorre quando:

- nao ha titulos selecionados;
- o intervalo de datas e muito restritivo;
- nenhum vencimento permanece selecionado apos o refinamento.

### Valores numericos aparecem incorretos

Confirme se o parser continua convertendo corretamente separadores decimais e tipos numericos.

## Licenciamento e fonte dos dados

Os dados utilizados no projeto sao publicos e provenientes do portal Tesouro Transparente. Antes de publicar ou redistribuir o app, recomenda-se verificar:

- a politica de uso dos dados publicos;
- necessidade de citacao da fonte;
- eventuais mudancas no endpoint oficial.

## Resumo

Este webapp foi desenvolvido para oferecer uma leitura profissional dos precos e taxas dos titulos publicos, com foco em visualizacao clara, filtros objetivos e estrutura pronta para evolucao.

A combinacao entre Streamlit, Pandas e Plotly torna o projeto simples de manter, rapido de executar e suficientemente flexivel para crescer para outros modulos analiticos.
