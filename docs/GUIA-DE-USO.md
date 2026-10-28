# Guia de uso do LoonieMind

## Abrir e fechar

No Windows, abra **Iniciar LoonieMind.cmd** na pasta do projeto. Na primeira vez, tenha Python 3.12 instalado e acesso à internet para baixar as bibliotecas. Depois da instalação, não é necessário acesso à internet para usar as telas, gráficos, importações ou modelos.

A aplicação abre em **http://127.0.0.1:8765**. Mantenha a janela de execução aberta durante o uso. Para encerrar o servidor, use `Ctrl+C` nessa janela. Fechar apenas a aba do navegador mantém o servidor em execução. O inicializador reconhece uma instância já aberta na mesma porta.

Caso prefira iniciar manualmente, siga o README. `python run.py --no-browser` evita abrir uma nova aba; `--port 8766` escolhe outra porta.

## Começar

Escolha **Criar minha empresa** para cadastrar nome, descrição, saldo inicial e data de referência. O saldo inicial representa o dinheiro disponível antes das movimentações da data escolhida; os lançamentos a partir dessa data, inclusive, compõem o saldo atual. Lançamentos anteriores continuam visíveis no histórico.

Ou selecione **Explorar demonstração**. Será criada a empresa fictícia Estúdio Aurora, com 210 dias de movimentações sintéticas e um classificador demonstrativo. Dados e modelos sintéticos são identificados na tela. Empresas novas começam sem movimentações e não usam o modelo de outra empresa.

## Importar uma planilha

1. Abra **Importação**. Baixe um modelo Excel/CSV se precisar de uma estrutura inicial.
2. Selecione ou arraste um arquivo CSV, XLS ou XLSX, com até 10 MB, 10.000 linhas e 100 colunas na aba.
3. Confira o cabeçalho e o mapeamento de data, descrição e valor. É possível usar uma coluna de valor ou as duas colunas de entrada/crédito e saída/débito.
4. Se o arquivo tiver várias abas, escolha a aba correta. Ajuste linha do cabeçalho, formato dos valores e das datas quando necessário e clique em **Atualizar prévia**.
5. Confira as linhas e erros. A prévia mostra até 30 linhas válidas e 200 erros; a confirmação processa toda a aba. Formatos de data suportados: DD/MM/AAAA, MM/DD/AAAA quando selecionado, e ISO AAAA-MM-DD.
6. Confirme a importação. Para importar apenas as linhas válidas ou manter transações semelhantes ao histórico, marque a autorização correspondente.

Valores brasileiros, como `1.234,56`, e decimais, como `1234.56`, são suportados. `1.234` é ambíguo no modo automático: selecione o formato brasileiro para interpretá-lo como 1.234 reais. Frações de centavo são arredondadas comercialmente. Não são executadas fórmulas/macros; planilhas protegidas por senha não são aceitas.

O tipo pode ser Receita/Entrada/Crédito/1 ou Despesa/Saída/Débito/2. Um valor negativo indica despesa. Um positivo sem tipo só é tratado como receita se você confirmar que a coluna é um extrato assinado; caso contrário fica pendente. Tipos ausentes não entram no saldo até serem revisados.

Somente movimentações já realizadas são aceitas. Datas futuras, valores zero, descrições vazias e conflitos entre sinais/tipos aparecem como erros. Para cancelar a gravação, abandone a prévia; o arquivo permanecerá disponível para continuar no histórico de importações.

A mesma aba do mesmo arquivo não pode ser confirmada duas vezes para uma empresa. Se precisar reprocessá-la, use **Desfazer** no histórico. Essa ação remove também as correções feitas nos lançamentos vinculados; leia a confirmação antes de continuar. O arquivo e a auditoria permanecem disponíveis.

## Classificar e revisar

Em **Classificação**, clique em **Gerar sugestões**. Selecione as sugestões adequadas e confirme individualmente ou em lote. Para corrigir tipo, categoria, valor ou descrição, use o botão de edição. Uma movimentação confirmada não é reescrita ao gerar novas sugestões.

**Treinar modelo** permite usar o histórico revisado desta empresa ou uma base sintética identificada. O treino revisado exige pelo menos 24 exemplos, duas classes combinadas de tipo/categoria e quatro grupos de descrições distintos por classe. Se a base ainda não atender aos requisitos, a aplicação explica o que falta. Sem modelo, existem sugestões simples por palavras-chave, identificadas como regras.

O score é a saída bruta do classificador, sem calibração de probabilidade; não é uma garantia de acerto. F1 macro mede a avaliação interna em exemplos separados do treino. Um bom resultado em dados sintéticos não demonstra qualidade em dados reais. Treinar novamente substitui o modelo e limpa sugestões pendentes antigas, preservando revisões confirmadas.

## Acompanhar o caixa

O **Dashboard** mostra saldo consolidado, receitas/despesas do período, resultado, lançamentos recentes, despesas por categoria e alertas calculados. As variações comparam o período escolhido com um período anterior da mesma duração; quando o anterior é zero, não se inventa uma porcentagem.

O saldo é independente do filtro de período do dashboard. Registros sem tipo são excluídos dos totais e sinalizados. Os dias de cobertura usam o saldo disponível dividido pela média de saídas realizadas nos últimos 30 dias. Não são uma garantia de prazo de caixa.

Em **Lançamentos**, busque, filtre, registre, edite ou exclua movimentações. Edições/exclusões ficam na auditoria. Excluir um lançamento não tem recuperação por lixeira; use um backup ou o arquivo original se precisar restaurá-lo.

## Ver previsões

**Previsão de caixa** mostra 7, 30, 60 ou 90 dias. São necessários ao menos 28 dias de histórico com movimentações recentes; se a última movimentação tiver mais de 7 dias, atualize os arquivos antes de prever. Dias sem registros dentro da série são considerados sem movimentação: confira a cobertura completa dos arquivos.

Com pelo menos 90 dias e 20 dias com valores positivos por série, o LightGBM é comparado a uma referência de 7 dias em um teste cronológico. Cada série escolhe o método com menor MAE; o método e o erro são exibidos. Valores previstos são estimativas e ficam separados do realizado. A edição do saldo/histórico invalida a previsão em cache.

## Exportar e guardar uma cópia

Em **Exportação**, escolha lançamentos ou previsão, aplique filtros/horizonte e baixe XLSX ou CSV. O CSV usa UTF-8 com BOM, ponto e vírgula e decimais brasileiros. O XLSX inclui filtros, cabeçalho e valores numéricos. Textos que possam ser interpretados como fórmulas são tratados como texto.

**Baixar backup completo** gera um ZIP com todas as empresas, lançamentos, categorias, auditoria e arquivos originais. Ele contém dados financeiros: guarde-o em um local apropriado. Os modelos não são incluídos; podem ser treinados novamente a partir do histórico revisado.

## Restaurar um backup

A restauração usa uma pasta nova e não sobrescreve o banco atual. Feche o servidor e, na pasta do projeto, execute no PowerShell:

```powershell
.\.venv\Scripts\python.exe -m scripts.restore_backup "C:\caminho\looniemind-backup.zip" --destination "dados-restaurados"
$env:LOONIEMIND_DATA_DIR = (Resolve-Path "dados-restaurados").Path
.\.venv\Scripts\python.exe run.py
```

Substitua apenas o caminho do ZIP. A pasta de destino precisa ser nova. O restaurador verifica integridade, versão e caminhos, recria o esquema confiável da aplicação e copia os dados; não executa o SQL do backup recebido. O limite operacional do restaurador é 200 MB/10.000 arquivos. Para voltar à base padrão, encerre o servidor, remova a variável `LOONIEMIND_DATA_DIR` dessa sessão e inicie novamente.

## Resolver problemas comuns

- **Não abre:** confira Python 3.12 e as mensagens na janela de execução. Reinstale as dependências com o arquivo de versões fixadas se necessário.
- **Porta ocupada:** uma instância já aberta pode ser reutilizada; para outra aplicação na mesma porta, escolha `--port` diferente.
- **Valor ambíguo:** confirme o formato brasileiro/decimal e atualize a prévia.
- **Saldo não bate:** confira saldo inicial, data de referência, cobertura dos arquivos, reimportações e lançamentos sem tipo.
- **Sem previsão:** confira quantidade de dias e atualização do histórico; dados de demonstração podem ser explorados em uma empresa separada.
- **Modelo inválido após atualizar bibliotecas:** mantenha as versões fixadas e treine novamente. Somente artefatos criados pela aplicação devem ser carregados.

O projeto foi configurado para um operador local. Expor o servidor à rede/internet, compartilhar os arquivos entre computadores ou usar vários operadores simultâneos exige outra revisão de arquitetura.
