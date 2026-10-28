# Capítulo 3: Treinamento do modelo

> O texto abaixo registra a proposta inicial. O treinamento foi implementado em `looniemind/models.py`: TF-IDF + LightGBM, avaliação por grupos, revisão humana e previsão com teste cronológico contra uma referência sazonal. A demonstração tem 576 exemplos sintéticos/12 classes e não comprova desempenho real. Consulte [dados, parâmetros e métricas da implementação](../ARQUITETURA.md) e o [guia de uso](../GUIA-DE-USO.md) para os comandos e requisitos atuais.

## 1. Objetivo do capítulo

Documentar os dois modelos de aprendizado de máquina do projeto: a classificação financeira e a previsão financeira.

## 2. Classificação financeira

- Tipo de modelo: supervisionado
- Algoritmo: LightGBM
- Representação do texto: TF-IDF (Scikit-learn)
- Objetivo: classificar automaticamente receitas, despesas e categorias

### O que é TF-IDF

TF-IDF é uma técnica que transforma textos em números para que um modelo de Machine Learning consiga analisá-los. O Scikit-learn é a biblioteca que fornece a implementação do TF-IDF.

### Como as categorias viram números

O TF-IDF trabalha apenas com o texto da descrição de cada lançamento: é a entrada do modelo. A categoria é o que o modelo precisa prever, e o LightGBM representa cada categoria por um número inteiro.

| Etapa | O que acontece |
|---|---|
| Entrada | O TF-IDF converte a descrição do lançamento em números |
| Saída do modelo | O modelo prevê o código numérico da categoria |
| Resultado | O código é convertido de volta para o nome da categoria |

No banco de dados, o campo categoria da tabela Lancamentos continua sendo VARCHAR. Isso é possível porque o SQLite guarda números em campos de texto. Os detalhes e o cuidado com a conversão na leitura estão no capítulo 02.

## 3. Previsão financeira

- Algoritmo: LightGBM Regressor
- Apoio: Pandas
- Objetivo: prever receitas e despesas futuras com base no histórico e em variáveis temporais

## 4. Dados de treinamento

- Origem dos dados: (a definir)
- Quantidade de exemplos: (a preencher)
- Categorias usadas: (a definir)
- Separação entre treino e teste: (a definir)

## 5. Avaliação

- Métricas da classificação: (a definir)
- Métricas da previsão: (a definir)
- Resultados obtidos: (a preencher)

## 6. Pontos em aberto

- Definir a base de dados rotulada para o treinamento.
- Escolher as métricas de avaliação dos dois modelos.
- Definir como os modelos treinados serão salvos e carregados pela aplicação.

[Voltar ao índice](../../README.md)
