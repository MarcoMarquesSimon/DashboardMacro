# WebApp Tesouro Direto

## Visao geral

Este projeto e um webapp desenvolvido em Streamlit para analise visual de precos e taxas de titulos publicos do Tesouro Direto.

O aplicativo foi pensado para um uso profissional: interface limpa, foco em legibilidade, filtros objetivos e visualizacoes que ajudam a comparar diferentes combinacoes de titulo e vencimento ao longo do tempo.

A aplicacao consome diretamente a base publica do Tesouro Transparente, trata os dados e entrega um dashboard interativo para acompanhamento de:

- taxa de compra
- taxa de venda
- PU de compra
- PU de venda
- PU base

Cada serie exibida no grafico principal e tratada como uma combinacao unica de:

- tipo de titulo
- data de vencimento

Isso evita misturar curvas distintas dentro do mesmo grupo de titulo e torna a leitura financeira mais correta.

---

## Principais funcionalidades

### Dashboard de Tesouro Direto

- filtro por tipo de titulo
- filtro por intervalo de data base
- filtro por vencimentos, com pre-selecao de titulos ainda vigentes
- opcao para incluir titulos com vencimento passado
- grafico temporal principal por titulo + vencimento
- marcacoes de minimo, maximo e valor atual quando a quantidade de series permite
- painel lateral de KPIs compactas
- tabela detalhada com modo enxuto e colunas adicionais opcionais
- exportacao dos dados filtrados em CSV

### Estrutura preparada para expansao

A aplicacao ja possui uma segunda pagina chamada **Analise Macro**, mantida propositalmente em branco para futuras extensoes do projeto.

Isso facilita a evolucao para um repositorio com mais de um dashboard, preservando a mesma identidade visual.

---

## Arquitetura do projeto

O projeto foi organizado em dois arquivos principais:

```text
.
|- app.py
|- dados_tesouro.py
|- requirements.txt
|- README.md
```

### `dados_tesouro.py`

Responsavel pela camada de carga e tratamento inicial dos dados.

Funcoes principais:

- leitura do CSV publico do Tesouro Transparente
- conversao das colunas de data
- conversao das colunas numericas
- retorno de um `DataFrame` pronto para uso no dashboard

### `app.py`

Responsavel pela interface, logica de filtros e exibicao dos componentes visuais.

Blocos principais:

- configuracao da pagina
- definicao da paleta e do estilo visual
- funcoes auxiliares de formatacao e resumo
- carregamento com cache
- navegacao entre dashboards
- dashboard do Tesouro Direto
- pagina reservada para Analise Macro

---

## Fonte de dados

A base utilizada vem do portal **Tesouro Transparente** e e consumida diretamente por URL.

Dataset utilizado:

- `precotaxatesourodireto.csv`

Estrutura esperada da base:

- `Tipo Titulo`
- `Data Vencimento`
- `Data Base`
- `Taxa Compra Manha`
- `Taxa Venda Manha`
- `PU Compra Manha`
- `PU Venda Manha`
- `PU Base Manha`

---

## Requisitos

### Requisitos de software

- Python 3.10 ou superior
- `pip` instalado
- acesso a internet para leitura do CSV remoto

### Dependencias Python

As dependencias estao listadas no arquivo `requirements.txt`.

Pacotes principais:

- `streamlit`
- `pandas`
- `plotly`

---

## Instalacao local

### 1. Clonar o repositorio

```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
```

### 2. Criar ambiente virtual

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux ou macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Executar a aplicacao

```bash
streamlit run app.py
```

Apos a execucao, o Streamlit abrira o aplicativo localmente no navegador.

---

## Como usar

### 1. Selecionar os titulos

Na barra superior, escolha um ou mais titulos para analise.

### 2. Definir o intervalo de datas

Use os campos de calendario para determinar:

- data inicial
- data final

Esses filtros atuam sobre a coluna `Data Base`.

### 3. Escolher a metrica principal

Selecione a metrica que sera plotada no grafico principal:

- Taxa Compra Manha
- Taxa Venda Manha
- PU Compra Manha
- PU Venda Manha
- PU Base Manha

### 4. Refinar os vencimentos

No painel expansivel de vencimentos:

- por padrao, o app pre-seleciona apenas vencimentos ainda ativos
- o usuario pode optar por incluir vencimentos passados

### 5. Interpretar o grafico

Cada curva representa uma serie unica no formato:

`Tipo Titulo - Data Vencimento`

Quando ha poucas series simultaneas, o app adiciona marcacoes de:

- minimo
- maximo
- valor atual

### 6. Consultar a tabela detalhada

A tabela final pode ser visualizada de forma mais enxuta ou expandida com colunas adicionais.

### 7. Exportar os dados filtrados

Use o botao de download para baixar um CSV com os dados atualmente filtrados.

---

## Decisoes de design

O dashboard foi desenhado com foco em:

- legibilidade em ambiente profissional
- baixa poluicao visual
- contraste elevado
- hierarquia clara entre grafico, KPIs e tabela
- navegacao simples

### Paleta adotada

- `#0F46AB` - azul principal
- `#061630` - fundo principal
- `#E6E6E6` - texto claro
- `#2B2B2B` - superficies e cards

### Estrategia visual

- o grafico principal recebe a maior area da tela
- as KPIs ficam compactas e alinhadas verticalmente
- a sidebar e usada apenas para navegacao entre dashboards
- os filtros principais ficam no topo, em faixa horizontal

---

## Regras de negocio implementadas

### Series independentes por vencimento

Mesmo quando o mesmo tipo de titulo aparece com varios vencimentos, o app trata cada vencimento como uma serie separada.

Isso evita agregar informacoes que deveriam permanecer distintas.

### Vencimentos ativos como padrao

O filtro de vencimentos pre-seleciona apenas titulos ainda vigentes.

Essa escolha melhora a experiencia padrao do usuario e reduz ruido visual, mantendo os vencidos disponiveis apenas quando necessario.

### Controle de poluicao visual no grafico

As marcacoes de minimo, maximo e atual aparecem de forma adaptativa:

- com poucas series, o detalhe e exibido
- com muitas series, o app prioriza limpeza visual

---

## Personalizacao

### Alterar a paleta de cores

As cores centrais estao no inicio do `app.py`:

```python
COR_PRIMARIA = "#0F46AB"
COR_FUNDO = "#061630"
COR_TEXTO = "#E6E6E6"
COR_SUPERFICIE = "#2B2B2B"
```

### Alterar a metrica padrao

A metrica inicial e definida no `selectbox` com o parametro `index=0`.

### Alterar a URL da base

A URL do dataset esta centralizada em:

```python
URL = "..."
```

Se o endpoint mudar, basta atualizar esse valor.

### Adicionar novas paginas

A estrutura com `radio` na sidebar permite incluir novas secoes facilmente, como:

- curva de juros
- comparacao entre indexadores
- indicadores macro
- analise historica por titulo especifico

---

## Deploy no Streamlit Community Cloud

### Estrutura recomendada do repositorio

Para deploy no Streamlit Community Cloud, mantenha:

- `app.py` como ponto de entrada
- `requirements.txt` na raiz do repositorio
- `dados_tesouro.py` no mesmo diretorio do app ou em modulo importavel

### Passo a passo

1. Suba o projeto para um repositorio no GitHub.
2. Garanta que o arquivo `requirements.txt` esteja presente.
3. Acesse o Streamlit Community Cloud.
4. Escolha o repositorio.
5. Defina `app.py` como arquivo principal.
6. Conclua o deploy.

### Observacoes de deploy

- o app depende de acesso externo ao CSV do Tesouro Transparente
- se houver mudanca na estrutura da base, o parser pode precisar de ajuste
- se forem adicionadas dependencias de sistema, sera necessario um `packages.txt`

---

## Troubleshooting

### O app nao abre

Verifique:

- se o ambiente virtual esta ativado
- se as dependencias foram instaladas
- se o comando executado foi `streamlit run app.py`

### Erro ao carregar os dados

Possiveis causas:

- indisponibilidade temporaria do endpoint remoto
- alteracao no layout do CSV
- indisponibilidade de internet

### Grafico vazio

Geralmente ocorre quando:

- o intervalo de datas nao possui registros
- nenhum titulo foi selecionado
- nenhum vencimento permaneceu marcado apos o refinamento

### Deploy falha no Streamlit Cloud

Confira:

- se `requirements.txt` esta na raiz do repositorio ou na pasta do arquivo principal
- se o arquivo de entrada esta correto
- se as bibliotecas necessarias estao listadas

---

## Roadmap sugerido

Algumas evolucoes naturais para este projeto:

- pagina de analise macroeconomica
- comparacao direta entre dois titulos
- renomeacao amigavel das metricas na interface
- filtros por faixa de taxa e faixa de PU
- destaque automatico de melhores e piores variacoes
- exportacao de relatorios em Excel ou PDF
- comparativos entre dias, semanas e meses

---

## Boas praticas recomendadas

- manter o arquivo de carga de dados separado da camada de interface
- centralizar cores, textos e configuracoes principais
- usar cache para evitar recarga desnecessaria
- testar o app com varios filtros simultaneos
- validar periodicamente se a estrutura do dataset remoto continua a mesma

---

## Licenca

Defina a licenca conforme a estrategia do projeto.

Se for um projeto pessoal ou interno, uma opcao simples e manter o repositorio privado ou adicionar uma licenca apropriada, como MIT, caso deseje compartilhamento aberto.

---

## Autor

Projeto desenvolvido para visualizacao profissional de dados do Tesouro Direto em Streamlit.

Se desejar, este README pode ser expandido com:

- badges de versao
- screenshots do app
- GIF demonstrando uso
- instrucoes de contribuicao
- changelog
