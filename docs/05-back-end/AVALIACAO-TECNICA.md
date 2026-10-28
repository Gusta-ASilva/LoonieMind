# Avaliação técnica do backend do LoonieMind

> Registro histórico da avaliação de 24/10/2026, anterior à implementação. O pedido passou a incluir a aplicação completa em 27/10. Consulte a [arquitetura atual](../ARQUITETURA.md) e as [decisões da v1](../DECISOES-E-ESCOPO.md) para o estado implementado.

Data: 24/10/2026. Revisão examinada: `2436e334e60b0a93e904a0df67a465b5e9b09966`, branch `main`.

Este documento registra o diagnóstico do repositório, recomendações e perguntas de definição. As recomendações ainda dependem das respostas do grupo; não constituem um contrato de implementação fechado.

## 1. Situação verificada

O projeto está na fase de documentação e modelagem. Há seis arquivos de documentação, dois diagramas do banco, um logo e o arquivo SQLite. Não há código executável de frontend ou backend, configuração de dependências, dados de treinamento, modelos salvos, testes, automação de integração ou instruções executáveis de instalação. Na consulta ao GitHub, havia apenas a branch `main`, sem issues ou pull requests abertos. O frontend mencionado pelo responsável precisa ser avaliado quando seu código estiver disponível.

O escopo documentado é uma aplicação local para pequenas empresas: importar Excel/CSV, normalizar dados, classificar receitas/despesas e categorias, prever fluxo de caixa, fornecer dados para um dashboard e exportar resultados. A documentação prevê Python, SQLite, Pandas, TF-IDF/Scikit-learn, LightGBM e uma interface Streamlit. Essas escolhas estão descritas, mas não implementadas.

Inspeção do banco `Database/LoonieMind.db`:

| Tabela | Registros | Relacionamento existente |
|---|---:|---|
| Empresas | 0 | Identificador, nome e descrição |
| Planilhas | 0 | Vinculada a Empresas |
| Lancamentos | 0 | Vinculada a Empresas; sem vínculo com Planilhas |

`PRAGMA integrity_check` retornou `ok`; a verificação de chaves estrangeiras não encontrou violações. O banco está vazio e sua versão de esquema é zero. Esses resultados não validam regras de negócio nem o funcionamento de uma aplicação.

O computador dispõe de Python 3.12.1, arquitetura AMD64, e SQLite 3.43.1 no Python inspecionado. As bibliotecas previstas para a aplicação não estão instaladas nesse interpretador; não foi examinado eventual ambiente Python externo. As versões Windows/Linux marcadas como compatíveis no README ainda precisam de validação prática.

## 2. Arquitetura e integração com o frontend

Recomendação: um único backend Python modular, com serviços de negócio independentes da interface. Separar leitura/normalização de arquivos, persistência, classificação, previsão, consultas financeiras e exportação. Evitar microserviços e serviços externos para a primeira entrega local.

| Situação do frontend | Integração recomendada |
|---|---|
| Streamlit, conforme a documentação | As telas chamam os serviços Python. Uma API HTTP separada é opcional, não um pré-requisito. |
| React, Vue ou outro frontend separado | Adicionar uma API FastAPI sobre os mesmos serviços, com contrato OpenAPI e exemplos de respostas. |
| Acesso pela internet com vários usuários | Reavaliar autenticação, autorização por empresa, hospedagem, armazenamento e concorrência antes da implementação. |

O backend deve entregar dados estruturados para os gráficos; a renderização fica com o integrante responsável pelo frontend. Um contrato mínimo entre os integrantes precisa cobrir:

- Empresas: cadastro, seleção e alteração de dados, incluindo saldo inicial e sua data de referência quando houver exibição de saldo de caixa.
- Importação: recebimento do arquivo, escolha da aba/cabeçalho, sugestão e confirmação do mapeamento, prévia, erros por linha e confirmação da gravação.
- Lançamentos: consulta paginada, filtros por empresa/período/tipo/categoria e correções manuais rastreáveis.
- Classificação: sugestão de tipo/categoria, estado de revisão e identificação da origem da sugestão.
- Indicadores: totais de entradas/saídas, variação líquida, séries por período, distribuição por categoria e saldo quando calculável.
- Previsão: horizonte, granularidade, receitas/despesas estimadas, método, versão do modelo e motivo quando o resultado estiver indisponível.
- Exportação: lançamentos e resultados selecionados em CSV/XLSX, com os mesmos filtros usados na consulta.

Antes do desenvolvimento das telas integradas, combinar nomes dos campos, datas ISO, representação exata de dinheiro, unidades, filtros, paginação, estados de processamento, mensagens de erro e exemplos de sucesso/erro. Se houver HTTP, documentar também endpoints, códigos de resposta e origens permitidas. Não há um contrato existente a preservar no repositório examinado.

## 3. Ajustes necessários no armazenamento e nas regras

| Achado | Consequência | Recomendação |
|---|---|---|
| `Lancamentos.valor` usa `REAL` | Arredondamentos em cálculos monetários | Normalizar com `Decimal` e persistir centavos inteiros; evitar `float` nos totais financeiros. |
| Lançamento não aponta para a planilha | Não é possível rastrear a linha importada ou desfazer uma importação com segurança | Registrar importação, aba e linha de origem, mantendo a consistência da empresa. |
| Ausência de identificação do conteúdo importado | Reimportar o arquivo pode duplicar valores | Identificar conteúdo e contexto de importação por empresa e impedir repetição da mesma confirmação. |
| Categoria e tipo obrigatórios sem estado de pendência | Dados sem classificação não têm um fluxo explícito | Prever uma área/estado de preparação e revisão antes de lançar valores indefinidos no histórico financeiro. |
| Categoria textual admite nomes ou códigos segundo a documentação | Misturar representações fragmenta os agrupamentos | Recomenda-se guardar nomes canônicos no banco e manter os códigos exclusivamente no artefato do modelo. Preserva-se a escolha documentada de categoria textual. |
| Sem saldo inicial e data de referência | Receitas menos despesas representam variação, não o saldo completo de caixa | Registrar a referência do saldo ou apresentar apenas a variação quando ela não existir. |
| Sem restrições para códigos/valores nem índices de consulta | Registros inválidos e consultas sem apoio de índices | Validar entrada, aplicar restrições coerentes e indexar empresa/data e vínculos de importação. |
| Sem migrações ou histórico de correções | Alterações futuras não são reproduzíveis | Versionar o esquema e registrar correções humanas e a versão dos modelos utilizados. |

As chaves estrangeiras existentes precisam ser habilitadas em cada conexão SQLite. SQL deve usar parâmetros, e a confirmação de uma importação deve ser transacional: falhas não podem deixar parte dos lançamentos gravada. Arquivo original e registros precisam de uma estratégia consistente de gravação e limpeza após falhas.

Manter o banco operacional, arquivos importados e logs fora do versionamento. O banco vazio atual pode servir como referência inicial, mas o esquema deve ser recriável por migrações. Prever backup e restauração compatíveis com o banco em uso. As alterações propostas precisam ser alinhadas com eventuais exigências acadêmicas de manter o modelo original.

Também é necessário definir se os dados representam pagamentos/recebimentos realizados ou valores a pagar/receber, qual é a moeda e como tratar estornos, transferências e sinais negativos. Um valor positivo isolado não informa se houve entrada ou saída; sinais, colunas de débito/crédito e tipos informados devem ser conciliados antes de usar uma sugestão de IA.

## 4. Importação, classificação e previsão

### Importação

Implementar leitura de CSV, XLS e XLSX, formatos citados na documentação, com os leitores adequados — por exemplo, `openpyxl` para XLSX e `xlrd` para XLS. Definir limites de tamanho/linhas após conhecer o volume esperado.

A importação deve reconhecer aliases de cabeçalho e permitir confirmação do usuário. Tratar separadores de CSV, codificação, vírgula/ponto decimal, valores monetários brasileiros, datas brasileiras/ISO, células vazias e abas de Excel. Formatos ambíguos devem aparecer na prévia para confirmação, sem conversão silenciosa.

Mostrar erros com aba/linha/campo e um resumo conciliável de registros válidos, inválidos e suspeitos de duplicidade. Não executar macros nem fórmulas; células calculadas sem valor utilizável precisam de tratamento explícito. Se existir importação parcial, ela deve ser uma escolha explícita com relatório das linhas rejeitadas.

Repetir o mesmo arquivo para a mesma empresa deve ser controlado. Lançamentos iguais em arquivos diferentes são candidatos à revisão, não motivo suficiente para exclusão automática: duas transações legítimas podem ter os mesmos campos.

### Classificação financeira

Falta definir uma base rotulada representativa, a lista de categorias, o responsável pela rotulagem e o responsável pelo treinamento. Sem essas definições não é possível atestar qualidade do classificador. Dados sintéticos podem apoiar a demonstração e os testes, identificados como tais; não comprovam desempenho em empresas reais.

Manter TF-IDF e LightGBM como proposta inicial do projeto, com pré-processamento consistente entre treino e uso. Treinar o vocabulário apenas no conjunto de treino e separar descrições repetidas/relacionadas para reduzir vazamento na avaliação. Medir F1 macro, precisão/recall por classe e matriz de confusão; avaliar tipo e categoria separadamente. Comparar com uma referência simples antes de afirmar benefício do modelo.

Salvar juntos a representação de texto, os modelos, o mapeamento das classes, versões de dependências e metadados de avaliação. Carregar apenas artefatos de origem controlada. Probabilidade bruta não deve ser apresentada como uma garantia de acerto; definir o limiar de revisão a partir da validação.

Permitir correção manual, preservar o que foi confirmado pelo usuário e registrar a origem de cada classificação. Uma correção não deve disparar treinamento automático sem controle. Quando o modelo estiver ausente ou o resultado for insuficiente, permitir revisão manual e informar o estado ao frontend.

### Previsão financeira

Falta definir frequência dos dados, horizonte desejado, extensão do histórico e critérios de qualidade. Preparar séries separadas de receitas e despesas e construir variáveis temporais usando apenas informações disponíveis até a data da previsão. Diferenciar ausência de dados de um período comprovadamente sem movimentação.

Avaliar o LightGBM Regressor com separação cronológica e testes em períodos futuros, comparando com uma referência simples, como repetição sazonal ou média recente. Medir MAE em reais e uma métrica agregada adequada, como WAPE quando seu denominador for diferente de zero. Não definir metas numéricas de qualidade sem conhecer a base.

O contrato deve informar método utilizado e período de treino. Com histórico insuficiente, retornar o motivo da indisponibilidade ou uma estimativa simples claramente identificada, conforme decisão do grupo. Não produzir um resultado fictício atribuído ao modelo. Faixas de incerteza exigem método e validação próprios.

Se houver saldo inicial, o saldo projetado considera o histórico realizado até a origem da previsão e depois acumula receitas previstas menos despesas previstas. Resultados estimados devem ficar separados das movimentações efetivamente realizadas. Reimportações e correções devem invalidar ou identificar previsões antigas.

## 5. Execução, confiabilidade e entrega

Criar ambiente virtual, configuração de dependências com versões reproduzíveis, configuração de caminhos e instruções de execução em um computador limpo. A aplicação local deve operar sem serviços de IA externos depois da instalação; confirmar se essa é também uma exigência do grupo.

Para uma entrega local com interface web, restringir o servidor à máquina por padrão. Acesso pela internet muda os requisitos e exige projeto de contas, permissões e isolamento dos dados. Validar uploads, nomes/caminhos de arquivo e limites de processamento; evitar registrar descrições financeiras e dados pessoais desnecessários em logs. Exportações devem tratar textos que programas de planilha poderiam interpretar como fórmulas, preservando os dados de negócio.

Disponibilizar logs úteis para diagnóstico, estados compreensíveis de processamento e indicação da disponibilidade dos modelos. Treinamentos devem ter comandos próprios e não rodar a cada abertura de tela. Só adicionar execução em segundo plano quando o volume e os tempos medidos exigirem isso.

O empacotamento Briefcase aparece no README como algo ainda a validar. Recomenda-se primeiro comprovar instalação e execução por ambiente Python; se um instalador for requisito da apresentação, sua compatibilidade com Streamlit/LightGBM deve ser validada cedo como uma etapa específica. Não considerar os formatos de instalador citados como entregas já garantidas.

Ordem sugerida, sujeita ao prazo e à divisão de tarefas:

1. **Definições e contrato:** obter frontend atual, amostras de arquivos, critérios acadêmicos e divisão de responsabilidade por dados/modelos.
2. **Fundação:** ambiente reproduzível, serviços, persistência, migrações, empresas e regras monetárias.
3. **Fluxo financeiro:** prévia/mapeamento, validação, confirmação transacional, histórico, correções, indicadores e exportação.
4. **IA:** base rotulada, treinamento, avaliação, persistência e integração da classificação e da previsão, com estados de indisponibilidade definidos.
5. **Integração e entrega:** ligar às telas, executar testes completos, validar backup, preparar demonstração e atualizar a documentação.

Cada etapa deve ter uma entrega verificável. O tempo necessário depende principalmente do estado do frontend, da disponibilidade dos dados e do requisito de instalador; ainda não há base para uma estimativa confiável.

## 6. Testes e critérios de aceite propostos

- Importar CSV com vírgula/ponto e vírgula, UTF-8/BOM e uma codificação legada acordada; ler XLS/XLSX e selecionar abas corretamente.
- Validar `1.234,56`, datas brasileiras/ISO, datas ambíguas, descrição vazia, valores/tipos conflitantes, arquivos corrompidos e tamanho acima do limite.
- Confirmar conciliação exata em centavos entre importação, banco, indicadores e exportação; conferir saldo com sua data de referência.
- Repetir importação e confirmação sem duplicar dados; manter transações legítimas iguais; simular falha de gravação sem persistência parcial.
- Isolar consultas e arquivos por empresa; preservar histórico ao reiniciar; recriar o esquema e restaurar um backup em ambiente de teste.
- Corrigir categoria/tipo, manter a revisão humana ao reprocessar e informar ausência/falha de um modelo sem bloquear funções financeiras independentes.
- Reproduzir a avaliação da classificação e da previsão, sem vazamento temporal/de rótulos; verificar a comparação com as referências simples e os casos sem dados suficientes.
- Exportar com filtros corretos e textos tratados com segurança; testar arquivos gerados em um leitor de planilhas.
- Executar o caminho completo a partir de uma instalação limpa: empresa → importação → conferência → classificação/revisão → dashboard → previsão ou justificativa de indisponibilidade → exportação.
- Validar o contrato com o frontend real e executar uma verificação automatizada de integração a cada mudança relevante.

Não foram executados testes de aplicação, treinamento, instalação das bibliotecas ou integração de telas: esses componentes ainda não existem no repositório avaliado.

## 7. Perguntas para fechar o escopo

As três primeiras perguntas foram enviadas no chat. As demais podem ser respondidas por escrito, e detalhes técnicos de baixo impacto podem ser definidos durante a implementação.

1. **Frontend:** qual tecnologia está sendo usada e onde está o código atual? Há telas, contratos de dados ou exemplos de respostas já combinados?
2. **Entrega e prazo:** é uma apresentação acadêmica local, uso local real ou aplicação na internet? Qual é a data e quais itens serão avaliados pelo professor?
3. **Responsabilidades de IA:** o backend deve incluir treinamento/avaliação dos modelos ou outro integrante os fornecerá? Já existem dados ou artefatos fora do GitHub?
4. **Arquivos de entrada:** vocês têm uma amostra anonimizada? Quais colunas, formatos, abas, quantidade de linhas por arquivo e meses de histórico precisam ser suportados?
5. **Significado financeiro:** os arquivos representam movimentações realizadas ou também contas futuras? Será apenas BRL e uma conta consolidada por empresa? Há estornos/transferências a tratar?
6. **Empresas e acesso:** um operador local poderá alternar entre várias empresas? Login, vários usuários ou acesso por outros computadores fazem parte da primeira entrega?
7. **Categorias e revisão:** há uma lista obrigatória de categorias? O usuário precisa criar categorias, corrigir lançamentos, inserir dados manualmente ou desfazer importações?
8. **Previsão e dashboard:** precisam de previsão diária, semanal ou mensal, e para quantos períodos? Quais indicadores são obrigatórios? O usuário poderá informar saldo inicial e data de referência?
9. **Liberdade de evolução:** podemos acrescentar tabelas/campos e corrigir o armazenamento monetário? Python, Streamlit, LightGBM e as três tabelas atuais são exigências imutáveis da disciplina ou escolhas revisáveis?
10. **Operação e distribuição:** quais sistemas precisam ser demonstrados/testados? Instalação por Python basta ou há exigência de instalador? Precisa funcionar totalmente offline após instalado?
11. **Dados e avaliação:** se não houver base rotulada, podemos usar dados sintéticos identificados para demonstração enquanto montamos uma base válida? Existe meta de qualidade estabelecida pelo professor ou pelo grupo?

## 8. Fontes

- [Repositório e escopo](https://github.com/GabrielIzi/LoonieMind/tree/2436e334e60b0a93e904a0df67a465b5e9b09966).
- [Modelagem documentada](https://github.com/GabrielIzi/LoonieMind/blob/2436e334e60b0a93e904a0df67a465b5e9b09966/docs/02-modelagem-banco-de-dados/README.md), conferida com o esquema e os diagramas do SQLite.
- [Modelos propostos e pendências de treinamento](https://github.com/GabrielIzi/LoonieMind/blob/2436e334e60b0a93e904a0df67a465b5e9b09966/docs/03-treinamento-do-modelo/README.md).
- [Arquitetura Streamlit](https://docs.streamlit.io/develop/concepts/architecture/architecture) e [recursos de contrato/validação do FastAPI](https://fastapi.tiangolo.com/features/).
- [Precisão numérica no SQLite](https://www.sqlite.org/floatingpoint.html) e [ativação de chaves estrangeiras](https://www.sqlite.org/foreignkeys.html).
- [Leitores de Excel no Pandas](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html).
- [Consistência e prevenção de vazamento no Scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html), [validação temporal](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) e [persistência de modelos](https://scikit-learn.org/stable/model_persistence.html).
