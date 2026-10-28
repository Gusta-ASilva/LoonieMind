# LoonieMind — Manual do sistema e IA

01 / VISÃO GERAL

LoonieMind

Manual do sistema, dados e inteligência artificial


## LoonieMind


O LoonieMind é uma proposta de solução de gestão financeira para pequenos negócios. Organiza movimentações, sugere categorias e estima o fluxo de caixa para apoiar a leitura do negócio. O material apresenta o projeto e sua implementação; não pressupõe empresa formalizada, clientes ou resultados comerciais já comprovados.

Formato de uso: aplicação web local. O programa Python executa neste computador e a interface abre no navegador em http://127.0.0.1:8765. O atalho de inicialização facilita o uso, mas esta versão ainda não é um instalador de aplicativo independente.

Tela real da versão 1.1 · empresa fictícia Aurora Comércio. Valores de demonstração, sem vínculo com empresas reais.

O ciclo principal

Cadastrar empresa e saldo de referência → importar e conferir planilha → revisar categorias → acompanhar saldo e projeção → exportar relatórios e backup. A confirmação humana faz parte do funcionamento da classificação.

Leitura do manual: importação (p. 2), regras financeiras (p. 3), treinamento (p. 4), previsão (p. 5), base de dados (p. 6), operação técnica (p. 7) e limites/evolução (p. 8).

02 / OPERAÇÃO E PLANILHAS

Do arquivo ao histórico

Importação em duas fases: conferir primeiro, gravar depois


## Do arquivo ao histórico


Em Minha empresa, crie um espaço e informe o saldo existente antes das primeiras movimentações da data de referência. Cada empresa mantém seus próprios lançamentos, categorias, arquivos e classificador. Alternar a empresa não mistura os dados.

Baixe o modelo Excel. Preencha Movimentacoes, que começa vazia. Exemplo_sintetico contém 240 registros fictícios e Orientacoes descreve o preenchimento. O modelo CSV contém exemplos e exige substituí-los pelos seus dados antes do uso real.


Campo | Regra e finalidade
Data, Descrição e Valor | Obrigatórios. Data realizada até hoje; descrição legível; valor positivo com até duas casas decimais.
Tipo e Categoria | Receita/Despesa e grupo financeiro. Tipo ausente deixa o valor fora dos totais; categoria ausente exige revisão.
Documento e Contraparte | Referência de nota/recibo e cliente, fornecedor ou instituição.
Centro de custo e Conta | Área responsável e conta/caixa. A leitura principal é o saldo consolidado da empresa.
Forma de pagamento | PIX, cartão, transferência, boleto, dinheiro ou outra descrição.
Competência | Mês econômico (AAAA-MM ou MM/AAAA). Não substitui a data de realização no fluxo de caixa.
Observações e ID externo | Contexto e referência no sistema de origem. ID externo não é chave de deduplicação automática.


Conferência, confirmação e correção

Selecione CSV, XLS ou XLSX. Confira aba, cabeçalho, formatos de data/valor e mapeamento das 13 colunas. Também são aceitas colunas separadas de entrada e saída. Valores positivos sem Tipo só indicam receita quando o usuário declara que o extrato é assinado. Valores negativos indicam despesa e conflitos são rejeitados.

A prévia mostra até 30 linhas válidas e os erros encontrados. Não modifica o saldo. Só a confirmação grava os registros, de forma transacional. A importação parcial exige escolha explícita; linhas inválidas precisam de correção posterior.

Mesmo arquivo, empresa e aba confirmados são bloqueados para evitar reimportação. Linhas semelhantes a lançamentos existentes geram aviso e exigem confirmação. Em Histórico de importações é possível desfazer todos os lançamentos associados a um arquivo. O histórico de auditoria registra a operação.

Limites: 10 MB, até 10.000 linhas, 100 colunas e 30 abas por arquivo. Divida bases grandes por cenário e ano. XLS antigo é aceito, mas o formato recomendado para intercâmbio é XLSX ou CSV UTF-8.

03 / LEITURA FINANCEIRA

Entender o saldo e o resultado

O período selecionado responde a uma pergunta diferente do saldo consolidado


## Entender o saldo e o resultado



Indicador | Como é calculado
Saldo consolidado hoje | Saldo inicial + receitas - despesas realizadas a partir da data de referência, incluindo esse dia.
Entradas / Saídas no período | Soma dos lançamentos com tipo definido dentro do período escolhido.
Resultado do período | Entradas do período - saídas do período. Não representa o total disponível em caixa.
Evolução do saldo | Saldo na abertura do gráfico + movimentos diários. Limite visual de 366 dias e da data de referência.
Visão Mensal | Entradas e saídas dos últimos 6 meses; a legenda informa que essa janela independe do filtro dos indicadores.
Projeção e menor saldo | Estimativa futura do histórico, com horizonte de 30 dias no dashboard. Não é saldo realizado.


Pendências e alertas que mudam a leitura

Lançamento sem tipo não entra em receitas, despesas ou saldo. O dashboard destaca tanto sua quantidade quanto seu valor total. Uma categoria ainda pendente, com tipo definido, já afeta o caixa, mas exige revisão para melhorar a análise por grupo.

Os alertas usam condições observáveis: saldo atual negativo, menor saldo futuro estimado negativo, revisões pendentes, concentração de despesas e falta de histórico recente. Não há um percentual arbitrário de “saúde financeira”. Uma concentração elevada não é, isoladamente, um problema: precisa de contexto do negócio.

A busca em Lançamentos encontra descrição, categoria, documento, contraparte e centro de custo. Correções e exclusões atualizam o saldo e invalidam a previsão armazenada. O histórico de auditoria mantém os eventos e, nas correções, os dados anteriores.

Relatórios para análise e compartilhamento

Excel financeiro: Resumo, Mensal, Categorias, Centros_de_custo e Lancamentos. Os totais por recorte são calculados a partir do detalhe. Saldo consolidado e saldo inicial são fotografias da empresa no momento da exportação e aparecem com contexto explícito. Recalcular um recorte do relatório não reconstrói todo o saldo da empresa.

Excel de projeção: Resumo, Previsao e Metodos. Exibe entradas, saídas, resultado e saldo diário estimados, além dos erros usados para comparar os métodos. CSV traz o detalhe para integração. Textos iniciados por caracteres de fórmula são protegidos como texto na exportação.

Editar um arquivo exportado não altera automaticamente o sistema. Para incluir alterações, importe o arquivo e selecione a aba Lancamentos. Confira a prévia e as duplicidades antes de confirmar.

04 / IA DE CLASSIFICAÇÃO

Como o modelo aprende

Aprendizado supervisionado local, com categorias confirmadas


## Como o modelo aprende


O classificador recebe a descrição e aprende uma classe composta por tipo e categoria, por exemplo “Despesa | Aluguel”. Documento, conta e valor são preservados no histórico, mas não são entradas do classificador nesta versão. O sistema não usa ChatGPT, não precisa de chave de API de IA e não envia descrições para serviços externos.


Etapa | Implementação atual
1. Preparar os exemplos | Histórico revisado da empresa, base sintética ou CSV rotulado. Mínimo de 24 exemplos, 2 classes e 4 descrições distintas por classe.
2. Separar famílias | Variações da mesma descrição ficam na mesma partição. Na base v2: 192 famílias em treino, 48 em validação e 48 em teste.
3. Converter o texto | TF-IDF de palavras (1–2 termos) e caracteres dentro de palavras (3–5 caracteres), reunidos em um vetor numérico. Vocabulário aprendido somente no treino durante a avaliação.
4. Treinar e medir | LightGBM Classifier: 90 árvores, até 15 folhas, profundidade 5, semente 42, 2 threads e ponderação equilibrada de classes. Parâmetros fixos nesta avaliação.
5. Publicar localmente | Após medir validação e teste, reajusta o modelo em toda a base disponível. Salva arquivo por empresa, versão, hash dos dados, bibliotecas e métricas.


Resultados efetivamente medidos na base v2

14.400 exemplos · 12 classes · 288 famílias. Treino: 9.600 exemplos (66,7%); validação: 2.400 (16,7%); teste: 2.400 (16,7%). As proporções efetivas decorrem do arredondamento por família. F1 macro na validação: 0,6034; no teste: 0,6766. A média macro dá o mesmo peso a cada classe; não é porcentagem geral de acertos nem probabilidade de retorno financeiro.

O resultado é desigual entre categorias. Por exemplo, Serviços teve F1 de aproximadamente 0,413 no teste. Os detalhes por classe estão em docs/relatorios/avaliacao-v1.1.json. Esses resultados são sintéticos e não comprovam qualidade em operações reais. Mais variações de um mesmo padrão não substituem diversidade de exemplos reais.

Uso, revisão e novo treinamento

Sem modelo, há sugestões por palavras-chave. Com modelo, a sugestão respeita o tipo já conhecido. O score exibido é uma saída do classificador, sem calibração de confiança; um score alto pode estar errado. O usuário confirma ou corrige. Lançamentos já revisados não são substituídos por novas sugestões.

A confirmação de uma categoria não treina o modelo na hora. Para incorporar novos exemplos, use Classificação → Treinar modelo → Histórico revisado. Isso substitui o artefato anterior da empresa e limpa sugestões pendentes. O lançamento financeiro já confirmado é preservado.

05 / IA DE PREVISÃO

Como o caixa futuro é estimado

Receitas e despesas são previstas separadamente e depois combinadas no saldo


## Como o caixa futuro é estimado


A previsão agrega os lançamentos por dia. Usa até 1.095 dias recentes; dias sem registros são tratados como movimento zero. Isso exige arquivos que cubram todo o período. Histórico cuja última movimentação tem mais de 7 dias é sinalizado como desatualizado e não gera projeção.

A partir de 28 dias, usa a repetição do padrão de 7 dias. A partir de 90 dias, com pelo menos 20 dias positivos na série, também avalia um LightGBM Regressor. Usa dia da semana, dia/mês, componente semanal, defasagens de 1/7/14/28 dias e médias móveis anteriores de 7/28 dias.

Os últimos 14 a 21 dias são separados cronologicamente. Cada previsão de teste usa apenas o passado e suas próprias previsões anteriores. Compara o erro absoluto médio (MAE) do LightGBM com o da referência semanal e escolhe o menor erro por série. Quando escolhido, o LightGBM é reajustado com todo o histórico disponível.

Saldo futuro = saldo realizado atual + entradas estimadas acumuladas - saídas estimadas acumuladas. Horizontes disponíveis: 7, 30, 60 ou 90 dias. A projeção é recalculada ao mudar o histórico/saldo ou o dia de referência; o classificador tem treinamento separado.

Validação cronológica de 7 a 27 de outubro de 2026


Cenário / série | MAE LightGBM | MAE referência | Escolhido
Aurora / receitas | R$ 135,89 | R$ 145,59 | LightGBM
Aurora / despesas | R$ 126,68 | R$ 2.078,73 | LightGBM
Horizonte / receitas | R$ 71,16 | R$ 130,54 | LightGBM
Horizonte / despesas | R$ 125,04 | R$ 1.797,11 | LightGBM
Studio / receitas | R$ 86,43 | R$ 86,42 | Semanal
Studio / despesas | R$ 151,67 | R$ 2.390,39 | LightGBM


MAE em reais por dia. No cenário Aurora, WAPE do método escolhido: 12,21% em receitas e 30,01% em despesas. WAPE é a soma dos erros absolutos dividida pelo total realizado. Não significa “87,79% de precisão” nem mede diretamente o erro acumulado do saldo.

O que a previsão ainda precisa considerar

A comparação usa uma única janela recente, que também escolhe o método; não é uma avaliação externa independente. Um pagamento excepcional pode mudar o caixa. A previsão não lê contratos nem uma agenda de vencimentos, não cria intervalo de confiança e não garante disponibilidade futura. Para uso real, são necessários testes em janelas sucessivas e monitoramento do erro realizado.

06 / DADOS DE DEMONSTRAÇÃO

Uma base maior e reproduzível

25.365 registros artificiais, com finalidades distintas


## Uma base maior e reproduzível



Conjunto | Dimensão e uso
Classificação rotulada | 14.400 descrições, 12 classes equilibradas (1.200 por classe), 288 famílias e 50 variações por família. Inclui tipo, categoria, grupo, fonte e ID do exemplo.
Aurora Comércio | 4.124 movimentações fictícias de comércio e serviços; saldo inicial de R$ 30.000,00.
Horizonte Varejo | 4.125 movimentações; queda recente de receitas e despesa excepcional; saldo inicial de R$ 20.000,00.
Studio Soluções | 2.716 movimentações de serviços, calendário útil e sazonalidade; saldo inicial de R$ 25.000,00.
Total financeiro | 10.965 movimentações. Geração cobre 1.095 dias de calendário até 27/10/2026; Studio começa a registrar em 30/10/2023.


O gerador usa semente 2702026 e nomes fictícios, sem CPF, CNPJ, contas bancárias ou dados pessoais reais. Introduz ciclos semanais, despesas mensais, sazonalidade, crescimento, ruído e um cenário de pressão no caixa. O volume serve para implementar e testar; não representa uma amostra de mercado.

Arquivos e separação correta

classificacao_rotulada.csv é a base do classificador e deve ser usada pelo treinamento, não importada como caixa. O campo grupo deve ser preservado para impedir que variações da mesma família apareçam em treino e teste.

financeiro/&lt;cenario&gt;_&lt;ano&gt;.csv traz movimentos com os 13 campos da planilha. Os arquivos já são separados por cenário/ano para facilitar a importação. Importe cada cenário em sua empresa, com o saldo inicial e a data de referência do manifesto. Não some os três cenários em uma única empresa.

manifesto.json registra quantidade, datas, classes, semente, tamanho e SHA-256 de cada arquivo. O ZIP reúne CSVs e manifesto. A demonstração ampliada fica isolada das empresas já existentes; o procedimento desta atualização conferiu a preservação das contagens anteriores.

Reproduzir e treinar na pasta do projeto

Gerar novamente:
.venv/Scripts/python.exe -m scripts.generate_dataset --end 2026-10-27

Treinar a base sintética por empresa:
.venv/Scripts/python.exe -m scripts.train_models --company ID --source synthetic

Treinar o CSV preservando os grupos:
.venv/Scripts/python.exe -m scripts.train_models --company ID --csv datasets/sintetica-v2/classificacao_rotulada.csv

Sem --end, as datas financeiras usam o dia da geração como referência. Para reproduzir os registros entregues, use --end 2026-10-27; semente igual com outra data altera calendário e arquivos.

07 / OPERAÇÃO TÉCNICA

Onde o sistema e os dados ficam

Execução local, separação por empresa e cópia de segurança


## Onde o sistema e os dados ficam



Camada | Responsabilidade
Interface | HTML, CSS e JavaScript locais. Dashboard, importação, lançamentos, classificação, previsão, exportação e empresas.
API e serviços | FastAPI/Uvicorn. Valida datas, tipos e valores, aplica operações e retorna dados para a interface. Contrato consultável em /api/docs.
Persistência | SQLite em data/looniemind.sqlite3. Valores financeiros em centavos inteiros; empresa associada a cada registro; arquivos de origem em data/uploads.
Modelos | scikit-learn + LightGBM. Artefatos de classificação em data/models, isolados por empresa. Previsão treinada/calculada em memória conforme histórico.
Auditoria e migração | Registra importações, revisões, exclusões e treinamento. Esquema v2 acrescenta os 8 campos complementares; snapshot anterior em data/backups.


Iniciar e usar

No Windows, execute Iniciar LoonieMind.cmd. Na primeira execução, o inicializador prepara o ambiente Python e instala dependências; isso pode exigir internet. Depois, a rotina operacional e a IA funcionam localmente com os recursos instalados. Para fechar o servidor, encerre a janela que mantém a aplicação em execução.

A interface e a API compartilham a mesma origem e o servidor escuta 127.0.0.1. O arquivo histórico vazio Database/LoonieMind.db foi mantido como referência. O banco operacional e os uploads não são enviados ao GitHub pelo funcionamento normal do sistema.

Backup e restauração

Exportação → Backup completo gera ZIP de todas as empresas, banco e arquivos de importação. Guarde uma cópia em local sob seu controle. Modelos não entram no backup e devem ser treinados novamente após a restauração.

Restaurar em pasta nova:
.venv/Scripts/python.exe -m scripts.restore_backup backup.zip --destination dados-restaurados

A restauração valida o conteúdo e não sobrescreve a pasta atual. Para utilizar a cópia, feche o servidor e inicie com LOONIEMIND_DATA_DIR apontando para a nova pasta. Confira empresa, saldo e lançamentos antes de retomar a operação.

Limites de acesso e privacidade

Esta edição não tem login, permissões por usuário, criptografia própria de banco ou sincronização entre computadores. Quem possui acesso à conta/pasta do computador pode acessar os arquivos. Não exponha este servidor na internet como se já fosse um serviço preparado para múltiplos usuários. Arquivos de modelo locais usam joblib e devem permanecer sob controle da própria aplicação.

08 / EVOLUÇÃO E REFERÊNCIAS

O que foi melhorado e o que vem depois

Registro da atualização e orientações para validar o uso real


## O que foi melhorado e o que vem depois



Entrega da versão 1.1 | Efeito prático
Dashboard reorganizado | Saldo, entradas, saídas e resultado em destaque; evolução diária com escala legível; projeção e qualidade do histórico.
Planilhas mais completas | 13 campos de entrada; exemplos separados; relatórios analíticos; dados complementares preservados na ida e volta.
Base e treinamento ampliados | 14.400 exemplos rotulados + 10.965 movimentos; treinamento executado e avaliação registrada com separação por famílias.
Documentação e apresentação | Manual, roteiro e PowerPoint curto, com distinção entre resultados sintéticos e qualidade a validar em produção.
Verificação | 40 testes automatizados aprovados na verificação da versão, incluindo importação, precisão, isolamento, backup, modelos e migração.


Próximos passos recomendados

1. Validar a rotina com o responsável financeiro: formatos reais de planilha, categorias, saldo inicial e cobertura das datas.
2. Reunir descrições reais revisadas, com origem e autorização de uso; medir erro por classe e separar empresas/períodos de teste.
3. Comparar modelos e regras, calibrar scores e avaliar rejeição de sugestões incertas; monitorar mudanças no padrão das descrições.
4. Avaliar previsões em várias janelas temporais, adicionar contas programadas e distinguir agenda de pagamentos de previsão estatística.
5. Antes de hospedagem compartilhada, implementar autenticação, permissões, proteção dos arquivos, política de retenção e restauração operacional.

Perguntas frequentes

O sistema aprende sozinho a cada clique? A revisão amplia a base confirmada. O classificador só é atualizado por um novo treinamento explícito.
Posso confiar no score como garantia? Não. O score não foi calibrado. Confira a descrição e a categoria.
Por que um modelo simples foi escolhido? Na previsão, a referência semanal pode errar menos que o LightGBM e ser selecionada. Isso ocorreu nas receitas do cenário Studio.
A demonstração prova o desempenho em qualquer empresa? Não. Os dados são artificiais e os padrões foram definidos pelo gerador.

Fontes e evidências

Implementação: looniemind/{api,db,domain,imports,services,models,synthetic,workbooks,backup}.py; interface web/; testes em tests/. Resultados: docs/relatorios/avaliacao-v1.1.json. Base e hashes: datasets/sintetica-v2/manifesto.json. Registro de decisões: docs/DECISOES-E-ESCOPO.md.

Referências técnicas primárias, consultadas em 27/10/2026:
<link href="https://scikit-learn.org/stable/modules/feature_extraction.html">scikit-learn · extração de atributos de texto</link>
<link href="https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html">scikit-learn · definição do F1</link>
<link href="https://lightgbm.readthedocs.io/en/stable/Python-API.html">LightGBM · classificadores e regressores da API Python</link>