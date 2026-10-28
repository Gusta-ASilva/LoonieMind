# LoonieMind — roteiro de apresentação

6 slides · duração planejada de 4min40s.

## Slide 1 · Inteligência financeira preventiva · 25s

A LoonieMind é um projeto acadêmico de inteligência financeira preventiva, pensado para pequenos negócios. A proposta é ajudar o empreendedor a entender o seu caixa e identificar possíveis dificuldades antes que elas comprometam a operação. O sistema reúne organização das movimentações, previsão estatística e confirmação humana das sugestões.

## Slide 2 · A empresa e sua proposta · 55s

O foco inicial são micro e pequenas empresas de comércio e serviços que ainda não têm uma equipe financeira dedicada. A proposta de valor é organizar os registros e usar o histórico para apoiar o planejamento do caixa. No plano de negócio, a receita é proposta por assinatura do software, complementada por diagnóstico e treinamento. Esse é o modelo comercial planejado. A versão que demonstramos hoje funciona localmente e recebe dados por planilhas. A oferta por assinatura e as integrações com bancos ou sistemas de gestão dependem da evolução do produto e da validação com clientes.

## Slide 3 · Visão do sistema · 45s

Esta é uma tela real da aplicação, usando a empresa fictícia Aurora Comércio. O fluxo começa com a importação da planilha, a conferência da prévia e a revisão das categorias. O saldo consolidado representa o caixa desde a referência. Entradas, saídas e resultado mostram o período selecionado. O gráfico permite acompanhar a evolução do saldo, enquanto as pendências e a projeção ficam ao lado. Documento, contraparte, centro de custo e conta ajudam a conferir cada lançamento. Os dados apresentados aqui são sintéticos.

## Slide 4 · Classificação com IA e revisão humana · 60s

A primeira aplicação de inteligência artificial é a classificação. A descrição é convertida em números por TF-IDF de palavras e caracteres. Um classificador LightGBM aprende a sugerir tipo e categoria. A base tem quatorze mil e quatrocentos exemplos em doze classes. Variações da mesma família de descrição ficam juntas, para evitar repetir o mesmo padrão no treino e no teste. O F1 macro medido no teste foi zero vírgula seis sete seis seis. Esse resultado é sintético e não garante a qualidade em empresas reais. A pessoa confirma ou corrige as sugestões. As correções só entram no modelo depois de um novo treinamento explícito.

## Slide 5 · Previsão e avaliação do erro · 55s

A segunda aplicação é a previsão do fluxo de caixa. O sistema estima receitas e despesas separadamente e combina as duas com o saldo atual. Com histórico suficiente, compara o LightGBM Regressor com a repetição do padrão semanal. Os dias mais recentes são reservados para uma validação cronológica, sem consultar o futuro. O método com menor erro é escolhido para cada série. No cenário Aurora, o erro médio diário das receitas foi de cerca de cento e trinta e seis reais, frente a cento e quarenta e seis da referência. Em outro cenário, o padrão semanal venceu. A projeção é uma estimativa e exige acompanhamento do caixa realizado.

## Slide 6 · Versão atual e evolução planejada · 40s

Hoje, o protótipo reúne importação, revisão, dashboard, previsão, relatórios e backup em uma aplicação local. O plano de negócio propõe evoluir essa solução para uma oferta por assinatura. Os próximos passos são validar as hipóteses com empresas-piloto, avaliar os modelos com dados reais e preparar a operação do serviço. A ideia central da LoonieMind é apoiar o pequeno empreendedor com uma leitura preventiva do caixa, mantendo transparência sobre os dados e sobre os limites da inteligência artificial.