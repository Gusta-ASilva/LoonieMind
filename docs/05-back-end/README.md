# Capítulo 5: Back-end

> Atualização de 27/10/2026: backend completo implementado em `looniemind/`, com FastAPI, SQLite operacional versionado, importação em duas fases, serviços financeiros, modelos e recuperação de backup. As pendências abaixo são da proposta original; o estado atual está em [Arquitetura operacional](../ARQUITETURA.md), [decisões](../DECISOES-E-ESCOPO.md) e [validação](../VALIDACAO.md).

## 1. Objetivo do capítulo

Documentar a lógica da aplicação: tratamento dos dados, classificação, previsão e armazenamento.

## 2. Tecnologias

| Tecnologia | Uso |
|---|---|
| Python | Linguagem de desenvolvimento da aplicação |
| SQLite | Armazenamento local do histórico |
| Pandas | Tratamento e organização dos dados |
| Scikit-learn | TF-IDF e apoio ao aprendizado de máquina |
| LightGBM | Modelos de classificação e de previsão |

## 3. Componentes

### Normalização de dados

Usa regras e aliases pré-cadastrados, junto com o Pandas, para identificar e mapear colunas, padronizar formatos e validar os dados.

### Classificação financeira

Usa o modelo supervisionado LightGBM com TF-IDF para classificar receitas, despesas e categorias. O treinamento está descrito no capítulo 3.

### Previsão financeira

Usa o LightGBM Regressor com o Pandas para prever receitas e despesas futuras. O treinamento está descrito no capítulo 3.

### Armazenamento

Guarda o histórico no SQLite, seguindo o modelo descrito no capítulo 2.

## 4. Estrutura do código

(a preencher: pastas e módulos do repositório)

## 5. Pontos em aberto

- Definir a estrutura de pastas e módulos do código.
- Definir a lista de aliases e regras iniciais da normalização.
- Planejar a integração futura com outras fontes de dados, como CRMs.

[Voltar ao índice](../../README.md)
