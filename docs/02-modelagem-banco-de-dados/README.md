# Capítulo 2: Modelagem do banco de dados

> Modelo original preservado como referência histórica. A v1 utiliza um banco operacional separado, com centavos inteiros, origem por importação, revisão, categorias e auditoria. O esquema atual e as diferenças estão em [Arquitetura operacional](../ARQUITETURA.md). O arquivo original vazio e seus diagramas não foram alterados.

## 1. Objetivo do capítulo

Documentar o modelo de dados usado para armazenar o histórico localmente em SQLite.

## 2. Modelo conceitual:

![Modelo conceitual](img/modelo-conceitual.jpeg)

## 3. Modelo lógico:

![Modelo lógico](img/modelo-logico.jpeg)

## 4. Relacionamentos

Uma empresa possui várias planilhas e recebe vários lançamentos.

| Entidade | Cardinalidade | Relacionamento | Entidade | Cardinalidade |
|---|---|---|---|---|
| Empresas | (1,1) | Possui | Planilhas | (0,n) |
| Empresas | (1,1) | Recebe | Lancamentos | (0,n) |

## 5. Tabelas

O banco de dados SQLite tem três tabelas. Empresas é a tabela central: cada planilha importada e cada lançamento financeiro pertencem a uma empresa.

Legenda da coluna Chave: PK é chave primária (identifica cada registro de forma única) e FK é chave estrangeira (aponta para o registro de outra tabela).

Os exemplos são ilustrativos e servem só para facilitar o entendimento.

### Empresas

Guarda as empresas cujos dados financeiros são analisados pela aplicação.

| Campo | Tipo | Chave | Para que serve | Exemplo |
|---|---|---|---|---|
| id_empresa | INTEGER | PK | Identificador único da empresa. É gerado automaticamente e usado pelas outras tabelas para ligar planilhas e lançamentos à empresa | 1 |
| nome | VARCHAR | | Nome da empresa, usado para identificá-la na interface e nos resultados exportados | Padaria Exemplo |
| descricao | VARCHAR | | Texto livre com informações sobre a empresa, como ramo de atividade e porte. Serve de contexto para quem usa a aplicação | Padaria de bairro com 5 funcionários |

### Planilhas

Registra cada arquivo Excel/CSV importado, para que se saiba de onde vieram os dados.

| Campo | Tipo | Chave | Para que serve | Exemplo |
|---|---|---|---|---|
| id_planilha | INTEGER | PK | Identificador único da planilha importada | 10 |
| id_empresa | INTEGER | FK para Empresas | Indica a qual empresa a planilha pertence. Uma empresa pode ter várias planilhas (ou nenhuma) | 1 |
| nome | VARCHAR | | Nome da planilha, normalmente o nome do arquivo importado | fluxo_caixa_setembro.xlsx |
| file_url | VARCHAR | | Caminho onde o arquivo importado fica guardado no computador. Permite reabrir ou reprocessar a planilha original | dados/importados/fluxo_caixa_setembro.xlsx |
| data | DATE | | Data em que a planilha foi importada para a aplicação. Permite saber quando cada arquivo entrou no histórico | 2026-10-16 |
| tipo | INTEGER | | Código do formato do arquivo importado (CSV, XLS ou XLSX). Define como a aplicação deve ler o arquivo. Os códigos estão na tabela "Formato do arquivo" abaixo | 1 |

### Lancamentos

Guarda cada movimentação financeira (receita ou despesa). É a tabela principal da aplicação: é com ela que o modelo treina, classifica e prevê o fluxo de caixa.

| Campo | Tipo | Chave | Para que serve | Exemplo |
|---|---|---|---|---|
| id_lancamento | INTEGER | PK | Identificador único do lançamento | 205 |
| id_empresa | INTEGER | FK para Empresas | Indica a qual empresa o lançamento pertence. Uma empresa pode ter vários lançamentos (ou nenhum) | 1 |
| descricao | VARCHAR | | Texto que descreve a movimentação, como veio na planilha. O TF-IDF transforma esse texto em números para o modelo classificar o lançamento | Pagamento fornecedor de farinha |
| categoria | VARCHAR | | Categoria financeira do lançamento, definida pela classificação automática ou informada na planilha. Também agrupa os gastos nos gráficos. O campo é de texto, mas o modelo trabalha com a categoria em número (veja a observação abaixo) | Matéria-prima |
| valor | FLOAT | | Valor monetário da movimentação, em reais. É sempre positivo: quem indica se o valor entra ou sai do caixa é o campo tipo | 1250.00 |
| data | DATE | | Data em que a movimentação ocorreu. É a base das variáveis temporais usadas pela previsão do fluxo de caixa | 2026-09-14 |
| tipo | INTEGER | | Código que indica se o lançamento é receita ou despesa. Como o valor é sempre positivo, é este campo que define se a movimentação entra ou sai do caixa. Os códigos estão na tabela "Tipo de lançamento" abaixo | 2 |

### Observação: categoria em texto no banco e em número no modelo

O modelo de classificação (LightGBM) trabalha com cada categoria representada por um número inteiro, enquanto o campo categoria da tabela Lancamentos é do tipo VARCHAR (texto). O grupo decidiu manter o campo como VARCHAR, sem alterar o banco de dados, porque números podem ser gravados normalmente em um campo de texto.

Como isso funciona na prática:

- **Dentro do modelo:** cada categoria tem um código numérico (por exemplo, 0 para Matéria-prima e 1 para Aluguel). Esse código existe só para o treinamento e para a previsão.
- **No banco:** o campo categoria guarda texto. O SQLite trata um campo VARCHAR como texto, então um número gravado nele é guardado como texto (o número 3 vira "3").
- **Na leitura:** o valor volta como texto. Antes de usá-lo como código no modelo, a aplicação precisa convertê-lo para número inteiro. Ao mostrar o resultado para o usuário, a aplicação converte o código de volta para o nome da categoria.
- **Consistência:** a aplicação deve gravar sempre o mesmo tipo de informação no campo (o nome da categoria ou o seu código), em todas as importações e classificações. Misturar os dois impede o agrupamento correto nos gráficos.

### Tabelas de códigos

Os campos tipo guardam um número inteiro. Estas tabelas dizem o que cada número significa. A aplicação deve usar sempre estes mesmos códigos, tanto ao gravar quanto ao ler os dados.

#### Formato do arquivo (Planilhas.tipo)

| Código | Formato | Extensão | Observação |
|---|---|---|---|
| 1 | CSV | .csv | Texto separado por vírgula ou ponto e vírgula |
| 2 | Excel antigo | .xls | Formato anterior ao Excel 2007 |
| 3 | Excel | .xlsx | Formato atual do Excel |

#### Tipo de lançamento (Lancamentos.tipo)

| Código | Tipo | Efeito no caixa | Exemplo |
|---|---|---|---|
| 1 | Receita | Entrada: aumenta o saldo | Venda de produtos |
| 2 | Despesa | Saída: diminui o saldo | Pagamento de fornecedor |

Regras de uso:

- O campo valor é sempre positivo. O saldo do fluxo de caixa é a soma das receitas (código 1) menos a soma das despesas (código 2).
- Para aceitar um novo formato de arquivo ou um novo tipo de lançamento, acrescente um novo código no fim da tabela, sem alterar os já existentes. Assim os dados antigos continuam válidos.

[Voltar ao índice](../../README.md)
