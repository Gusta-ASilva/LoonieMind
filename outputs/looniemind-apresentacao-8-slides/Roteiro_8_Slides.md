# LoonieMind — roteiro de apresentação

8 slides · duração planejada: 4min35s.

## Slide 1 · LoonieMind · 15s

A LoonieMind é um projeto de inteligência financeira preventiva para pequenos negócios. A proposta é organizar as movimentações e usar o histórico para apoiar uma leitura mais clara do caixa e das decisões do empreendedor.

## Slide 2 · A empresa e seu público · 30s

O público inicial são micro e pequenas empresas de comércio e serviços, especialmente quando não há uma equipe financeira dedicada. A proposta de valor combina organização dos registros, classificação e previsão do caixa. A aplicação demonstrada funciona localmente, recebe planilhas e mantém a confirmação humana das categorias sugeridas.

## Slide 3 · O desafio da gestão do caixa · 30s

A proposta parte de três situações: registros espalhados, tempo gasto para conferir e classificar lançamentos e dificuldade de entender como o caixa pode evoluir. O LoonieMind reúne os dados e apresenta informações para apoiar esse acompanhamento. São os problemas que orientam a solução, não resultados de uma pesquisa com clientes.

## Slide 4 · Visão do sistema · 40s

Esta é uma tela real do sistema com a empresa fictícia Aurora Comércio. A rotina começa pela importação da planilha, conferência da prévia e revisão das categorias. O saldo consolidado considera o histórico desde a referência. Entradas, saídas e resultado mostram o período selecionado. O gráfico acompanha o saldo, enquanto as pendências e a projeção ficam ao lado. Os dados desta demonstração são sintéticos.

## Slide 5 · Classificação com IA · 55s

Na classificação, a descrição é convertida em números por TF-IDF de palavras e caracteres. O LightGBM aprende a sugerir tipo e categoria. Foram usados quatorze mil e quatrocentos exemplos em doze classes, separando famílias de descrições entre treino, validação e teste. O F1 macro no teste foi zero vírgula seis sete seis seis. É uma avaliação sintética, sem garantia de qualidade em empresas reais. A pessoa confirma ou corrige as sugestões. Novas revisões só passam a integrar o modelo após um treinamento explícito.

## Slide 6 · Previsão de caixa · 50s

A previsão estima receitas e despesas separadamente e combina as duas com o saldo atual. Compara o LightGBM com a repetição do padrão semanal em uma janela cronológica reservada, sem consultar o futuro. O menor erro determina o método de cada série. No cenário Aurora, o erro médio diário das receitas foi cerca de cento e trinta e seis reais com LightGBM e cento e quarenta e seis com a referência. Em outro cenário, o padrão semanal venceu. A projeção é uma estimativa que precisa ser acompanhada.

## Slide 7 · Modelo de negócio proposto · 35s

O plano de negócio propõe receita recorrente por assinatura, com três planos mensais: Bronze, de cento e cinquenta reais; Prata, de duzentos e cinquenta; e Ouro, de quinhentos reais. Diagnóstico financeiro e treinamentos aparecem como serviços adicionais. Esses valores pertencem à proposta comercial. A versão mostrada aqui é local e ainda não tem cobrança por assinatura implementada.

## Slide 8 · Valor para o empreendedor · 20s

O valor da LoonieMind está em reunir um histórico organizado, uma visão clara do caixa e estimativas que podem ser conferidas. A inteligência artificial apoia a leitura dos dados, enquanto a revisão humana e a rastreabilidade ajudam o empreendedor a avaliar as informações antes de decidir.