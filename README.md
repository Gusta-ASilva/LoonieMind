# LoonieMind

Aplicação de inteligência artificial para organizar movimentações financeiras e prever o fluxo de caixa de pequenas empresas, rodando de forma simples e local.

Apresentação atualizada com o essencial do plano de negócio: [empresa e sistema · 8 slides / 4min35s](outputs/looniemind-apresentacao-8-slides/LoonieMind_Empresa_e_Sistema_8_Slides.pptx). [Registro da seleção e das alterações](docs/ATUALIZACAO-APRESENTACAO-EMPRESA.md).

[Baixar o pacote atualizado de materiais](outputs/looniemind-v11-20261027/LoonieMind_Materiais_Completos.zip): apresentação atual, roteiro correspondente, manual, planilhas e base sintética. Para obter o programa, baixe ou clone este repositório e siga as instruções de instalação abaixo.

## Atualização 1.1 · visualização, dados e apresentação

O dashboard prioriza saldo consolidado, entradas, saídas e resultado do período, com evolução diária e qualidade do histórico. As planilhas têm 13 campos de entrada e relatórios por mês, categoria e centro de custo. Os campos complementares são preservados na importação, edição, exportação e backup.

- [Manual completo do sistema e da IA](docs/MANUAL-SISTEMA-E-IA.md)
- [Roteiro para apresentação de 4min35s](docs/ROTEIRO-APRESENTACAO.md)
- [Materiais em PDF, Excel e PowerPoint](outputs/looniemind-v11-20261027/)
- [Base sintética e manifesto](datasets/sintetica-v2/manifesto.json)
- [Avaliação efetivamente medida](docs/relatorios/avaliacao-v1.1.json)

Em **Minha empresa → Base ampliada**, carregue três cenários fictícios isolados, preservando os dados existentes. A base v2 contém **14.400 exemplos rotulados** e **10.965 movimentações financeiras**. O classificador da demonstração Aurora foi treinado e obteve **F1 macro 0,6766** em 2.400 exemplos de teste com famílias separadas. Os dados são artificiais e esse resultado não comprova qualidade em empresas reais. Materiais também podem ser baixados em **Exportação**.

Reprodução:

```powershell
.\.venv\Scripts\python.exe -m scripts.generate_dataset
.\.venv\Scripts\python.exe -m scripts.train_models --company ID --source synthetic
```

Para reconstruir o ZIP dos materiais existentes, execute `python -m scripts.package_materials`. O empacotamento confere a apresentação de oito slides e os hashes da base sintética. As apresentações anteriores permanecem no repositório como histórico; o pacote contém somente a apresentação atual.

O banco é migrado para o esquema v2, com uma cópia prévia de bancos v1 em `data/backups/antes-da-versao-2.sqlite3`. Esta entrega inclui 41 testes aprovados; veja o registro atualizado em `docs/VALIDACAO.md`.

## Aplicação local · versão 1.1

Interface completa inspirada na referência de tela fornecida em 27/10/2026, com API Python, SQLite, importação CSV/XLS/XLSX, revisão de categorias, previsões, exportação e backup. A primeira abertura permite criar sua empresa ou explorar a empresa fictícia **Estúdio Aurora**, cujos dados e modelos demonstrativos são identificados na interface.

**Windows:** abra `Iniciar LoonieMind.cmd`. É necessário Python 3.12; na primeira instalação, o script baixa as dependências em um ambiente virtual do projeto. Nas próximas execuções, a aplicação funciona offline. O endereço padrão é **http://127.0.0.1:8765**.

Instalação manual no PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe run.py
```

Em Linux com Python 3.12 instalado, execute `sh iniciar.sh`. A validação local desta entrega foi feita em Windows x64; a verificação em Linux está configurada no CI e ainda precisa ser executada nesse ambiente.

- [Guia de uso e restauração de backup](docs/GUIA-DE-USO.md)
- [Mudança de escopo, decisões e limites da v1](docs/DECISOES-E-ESCOPO.md)
- [Arquitetura, regras financeiras e contratos](docs/ARQUITETURA.md)
- [Validação da entrega](docs/VALIDACAO.md)
- API local: `/api/docs`; contrato legível por ferramentas: `/api/openapi.json`.

O banco operacional fica em `data/looniemind.sqlite3`, fora do Git. O arquivo `Database/LoonieMind.db` e os diagramas originais foram preservados como referência histórica. Dados reais não devem ser enviados ao repositório. A demonstração usa dados sintéticos e não comprova desempenho em empresas reais.

### Verificação para desenvolvimento

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev-lock.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check looniemind scripts tests run.py
node --check web/app.js
```

| Informação | Detalhe |
|---|---|
| Disciplina | Inteligência Artificial, 2º semestre de 2026 |
| Professor | Edson Ceroni |
| Nome do grupo | LoonieMind |
| Status | v1 local implementada; evolução e validação registradas em docs |
| Repositório | https://github.com/GabrielIzi/LoonieMind |

## Identificação

| Logo do projeto |
|---|
| ![Logo LoonieMind](docs/logo.jpeg) |

| Integrantes |
|---|
| Gabriel Izidoro Felix dos Santos |
| David Ramos dos Santos |
| Felipe Silva Marcelino |
| Guilherme de Quadros Wendler da Costa |
| Gustavo Araujo |
| Lucas Evangelista |
| Rodrigo dos Anjos |

## Sumário

| Seção | Onde |
|---|---|
| Capítulo 01: Prototipação | [docs/01-prototipacao](docs/01-prototipacao/README.md) |
| Capítulo 02: Modelagem do banco de dados | [docs/02-modelagem-banco-de-dados](docs/02-modelagem-banco-de-dados/README.md) |
| Capítulo 03: Treinamento do modelo | [docs/03-treinamento-do-modelo](docs/03-treinamento-do-modelo/README.md) |
| Capítulo 04: Front-end | [docs/04-front-end](docs/04-front-end/README.md) |
| Capítulo 05: Back-end | [docs/05-back-end](docs/05-back-end/README.md) |
| Implementação operacional da v1 | [docs/ARQUITETURA.md](docs/ARQUITETURA.md) |
| Mudança de escopo e decisões | [docs/DECISOES-E-ESCOPO.md](docs/DECISOES-E-ESCOPO.md) |

## 1. Objetivo do trabalho

### Objetivo geral

Criar uma aplicação local que usa inteligência artificial para classificar as movimentações financeiras de uma empresa e prever o seu fluxo de caixa.

### Objetivos específicos

- Importar dados por Excel/CSV
- Armazenar o histórico localmente
- Classificar gastos e receitas
- Prever o fluxo de caixa
- Mostrar os resultados em gráficos/dashboard
- Exportar os resultados para Excel/CSV

A ideia é manter tudo simples e rodando localmente, deixando espaço para integrar outras fontes de dados no futuro, como CRMs.

## 2. Funcionamento da aplicação

1. O usuário importa uma planilha Excel ou CSV.
2. O sistema identifica as colunas, padroniza os formatos e valida os dados.
3. Os lançamentos são guardados no histórico local.
4. O modelo sugere tipo e categoria; o usuário confirma ou corrige a classificação.
5. A previsão compara o LightGBM com uma referência sazonal quando há histórico suficiente.
6. O dashboard mostra os resultados em gráficos.
7. O usuário exporta os resultados para Excel ou CSV.

O detalhamento de cada etapa está nos capítulos 03 e 05.

## 3. Softwares e bibliotecas utilizados

### Softwares
 
| Software | Versão | Como é usado | Quando é usado |
|---|---|---|---|
| Python | 3.12; validado com 3.12.1 | Backend e modelos | Desenvolvimento e execução |
| SQLite | 3.43.1 no Python validado | Histórico local versionado | Persistência e consultas |
| HTML, CSS e JavaScript | Módulos ES nativos | Interface e gráficos SVG | No navegador, sem etapa de build |
 
### Bibliotecas
 
| Biblioteca | Versão | Como é usada | Quando é usada |
|---|---|---|---|
| Pandas | 3.1.0 | Leitura e preparação de dados | Importação e séries temporais |
| Scikit-learn | 1.9.1 | TF-IDF, classes e avaliação | Treinamento e classificação |
| LightGBM | 4.7.0 | Classificação e regressão | Treinamento e previsão |
| FastAPI / Uvicorn | 0.162.0 / 0.54.0 | API e servidor da interface local | Toda a execução |
| Openpyxl / Xlrd | 3.1.5 / 2.0.2 | Excel atual e legado | Importação e exportação |

Dependências fixadas em `requirements-lock.txt`; ferramentas de teste em `requirements-dev-lock.txt`. A troca de Streamlit/Matplotlib por interface web/SVG está justificada no registro de decisões.
 
### Ferramentas de distribuição
 
| Biblioteca | Versão | Como é usada | Quando é usada |
|---|---|---|---|
| Scripts de inicialização | v1 | Ambiente virtual e execução por Python; `.cmd` no Windows e `.sh` no Linux | Instalação e uso local; instaladores nativos ficam para uma evolução |

## 4. Sistemas operacionais compatíveis

| Sistema | Compatível | Versão testada |
|---|---|---|
| Windows | Validado localmente | x64; Python 3.12.1 |
| Linux | A validar | CI configurada; não executada nesta entrega local |
| Android | Não | - |
| iOS | Não | - |
| Outros (macOS) | Não | - |

## 5. Elementos de Inteligência Artificial

| Princípio ou elemento | Utilizado | Justificativa |
|---|---|---|
| Aprendizado de máquina supervisionado | Sim | A classificação (LightGBM) e a previsão (LightGBM Regressor) são treinadas com dados históricos rotulados |
| Aprendizado de máquina não supervisionado | Não | Nenhum modelo busca agrupamentos sem rótulos |
| Aprendizado por reforço | Não | Não há agente que aprende por recompensa |
| Reconhecimento de padrão | Sim | O modelo reconhece padrões nas descrições dos lançamentos e nas variáveis temporais do histórico |
| Linguagem natural | Sim | O TF-IDF transforma as descrições dos lançamentos em números para o modelo |
| Banco de conhecimentos | Sim | O histórico fica no SQLite e as regras e aliases de normalização ficam pré-cadastrados |
| Poda | Não | Não é usada |
| Mecanismo de inferência | Não | Não há motor de regras com inferência |
| Encadeamento para frente | Não | Não é usado |
| Encadeamento para trás | Não | Não é usado |
| Sistema especialista | Não | As regras servem só para normalizar os dados |
| Sistema heurístico | Não | Não é usado |
| Modelo de busca | Não | Não é usado |
| IA generativa | Não | Não é usada |

## 6. Regras e quadro negro

### Quantidade de regras utilizadas

As regras de aliases estão em `looniemind/imports.py`. A classificação inicial sem modelo usa 12 palavras-chave, com origem identificada como regra. A demonstração supervisionada v2 usa 14.400 exemplos sintéticos de 12 classes combinadas de tipo/categoria e 288 famílias de descrições. O exemplo antigo de 576 registros permanece apenas nos metadados da demonstração v1 já existente.

### Domínio de conhecimento

Finanças de pequenas empresas: lançamentos de receitas e despesas, categorias financeiras e fluxo de caixa ao longo do tempo.

### Árvore de decisão

Os modelos LightGBM são conjuntos de árvores de decisão. Categorias, treinamento, validação e limites estão descritos no [capítulo 03](docs/03-treinamento-do-modelo/README.md) e na arquitetura operacional.
