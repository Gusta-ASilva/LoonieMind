# Mudança de escopo e decisões da versão 1

Data: 27/10/2026. Ponto de partida: commit `2436e334e60b0a93e904a0df67a465b5e9b09966`.

## Pedido e premissas

O responsável mudou o pedido de avaliação/implementação do backend para **desenvolvimento da aplicação completa**, incluindo frontend, e autorizou adaptações e acréscimos necessários, com registro. A referência foi uma imagem de dashboard enviada no chat; ela orienta a aparência e não constitui um requisito de integração bancária ou de um índice financeiro validado.

As perguntas da avaliação de 24/10 não receberam respostas. Para viabilizar a v1 foram adotadas, como decisões técnicas revisáveis: operação local por um usuário, várias empresas separadas, moeda BRL, movimentações realizadas, datas brasileiras/ISO, sem serviços externos de IA e sem autenticação de internet. Não se presume aprovação de hospedagem pública, envio de dados a terceiros ou publicação de alterações no GitHub.

## Decisões e justificativas

| ID | Decisão | Motivo e consequência |
|---|---|---|
| D01 | Entregar backend e frontend no mesmo projeto | Substitui a divisão anterior em que outro integrante cuidaria das telas. |
| D02 | FastAPI + HTML/CSS/JavaScript nativos, em lugar de Streamlit | Permite reproduzir menu, cartões, tabelas, estados e responsividade da referência; mantém todo o processamento financeiro em Python. Não exige Node para executar. |
| D03 | Gráficos SVG locais em lugar de Matplotlib no dashboard | Gráficos responsivos, sem imagens remotas, CDN ou serviços externos. |
| D04 | Preservar SQLite e criar um banco operacional separado | O banco original vazio não é alterado; o novo esquema é recriável e versionado. |
| D05 | Dinheiro em centavos inteiros | Remove erros de soma por ponto flutuante; parsing usa Decimal e arredondamento comercial. |
| D06 | Prévia → mapeamento → confirmação transacional | Evita gravação silenciosa de dados inválidos; importação parcial exige escolha explícita. |
| D07 | Manter tipo desconhecido pendente | Positivo isolado não significa receita; sem tipo, o registro fica fora dos totais até revisão. |
| D08 | Sugestões de categoria exigem confirmação | A IA não reescreve revisões humanas. Origem, score e versão são rastreados. |
| D09 | Demonstração sintética optativa e isolada por empresa | Possibilita usar o fluxo completo imediatamente sem fingir uma base financeira real. O classificador demonstrativo usa 576 exemplos e 12 classes. |
| D10 | Comparar LightGBM com referência sazonal | A previsão usa o método com menor MAE em um teste cronológico; com poucos dados pode retornar referência simples ou indisponibilidade. |
| D11 | Saldo inicial com data explícita | Permite calcular saldo real, em vez de chamar variação líquida de saldo. |
| D12 | Identificação do arquivo/aba e revisão de semelhantes | Mesma aba já confirmada não é duplicada. Lançamentos iguais em arquivos diferentes não são descartados automaticamente. |
| D13 | Acrescentar lançamentos manuais, empresas, categorias, auditoria e backup/restauração | Completa a rotina necessária para usar e corrigir o sistema. |
| D14 | Inicializadores Python para Windows e Linux | A v1 não depende de Briefcase e não afirma entregar MSI/DMG/AppImage. Linux possui CI configurada, ainda sem validação executada nesta sessão. |
| D15 | API e documentação servidas localmente | Mesma origem para telas/API, validação de Host/Origin e documentação sem CDN. |

## Adaptações visuais em relação à imagem

- Mantidos: menu lateral escuro, identidade LoonieMind, cores verde/teal, fundo claro, cartões financeiros, lançamentos, gráficos e despesas por categoria.
- Acrescentados: seleção de empresa, indicador de armazenamento local, onboarding, identificação da demonstração, filtros, busca, edição, estados vazios e menu em telas pequenas.
- Cartão de crédito, bandeira, últimos dígitos e limite foram substituídos por **conta consolidada e saldo de referência**, pois não há integração com bancos/cartões.
- O índice de “saúde financeira 82%” foi substituído por saldo mínimo projetado e dias de cobertura calculados. Não há um índice de risco inventado.
- Alertas de vencimento e “otimização de prazo” foram substituídos por avisos baseados no histórico: revisões pendentes, concentração de despesas, insuficiência de dados e possível saldo negativo. Não existem contas a pagar com vencimentos individuais nesta v1.
- O gráfico de caixa separa **Realizado** e **Projetado**; o usuário sabe quais valores são históricos e quais são estimativas.
- Os controles de busca, notificações e navegação são funcionais. Atalho `/` foca a busca; `Esc` fecha o menu e o painel de alertas.

## Limites explícitos

Não há login multiusuário, sincronização em nuvem, integração bancária/CRM, emissão fiscal, pagamentos, várias moedas ou gestão de contas futuras. Os modelos não oferecem garantia de acerto nem recomendam operações financeiras. O histórico sintético não comprova qualidade em empresas reais. O saldo consolidado não substitui conciliação bancária.

Não foi definido um prazo acadêmico nem uma meta externa de qualidade. Requisitos do professor, lista específica de categorias e eventual frontend externo poderão ser incorporados como nova revisão de escopo. As revisões do banco/modelos deverão continuar documentadas. A avaliação anterior permanece como registro histórico.

## Atualização 1.1 · visualização, planilhas e materiais

Solicitação: melhorar a leitura das informações, ampliar planilhas/base de treino e documentar a solução para uma apresentação de até cinco minutos.

- O dashboard passou a priorizar saldo consolidado, entradas, saídas e resultado; a janela de cada medida é explícita. O gráfico principal mostra saldo diário com escala adequada à variação. Visões mensal e projetada continuam disponíveis. Há valores excluídos por falta de tipo, pendências e data da última movimentação.
- Adicionados oito campos: documento, contraparte, centro de custo, conta, forma de pagamento, competência, observações e ID externo. Conta é um atributo do lançamento; esta versão não calcula saldo inicial individual por conta. Competência é informativa e não muda o regime de caixa.
- O modelo XLSX tem entrada vazia, 240 exemplos em aba separada e orientações/validação. CSV demonstrativo contém exemplos e está identificado. Excel financeiro apresenta resumo, mês, categoria, centro de custo e detalhe; projeção inclui métodos e erros. CSV conserva os dados complementares e a situação pendente.
- Migração SQLite v2 preserva registros e faz snapshot do banco v1. Restauração aceita versões 1/2 e continua usando pasta nova. Metadados de uma edição antiga são preservados quando o cliente não os envia.
- Base sintética v2: 14.400 descrições rotuladas, 288 famílias e 12 classes; três cenários com 10.965 movimentos e até 1.095 dias. CSVs financeiros são divididos por cenário/ano. Nomes e movimentações são fictícios, com semente/manifesto/hashes registrados.
- Classificador usa TF-IDF de palavras e caracteres com LightGBM e partições de treino, validação e teste por famílias. O arredondamento produz 66,7%/16,7%/16,7% nesta base, registrado por contagens. Não houve calibração do score nem ajuste de parâmetros sobre o teste. Treinamento da Aurora v2 foi executado; as outras duas empresas usam regras até um treino explícito. Todas possuem previsão financeira calculada a partir de seus próprios históricos.
- Previsão continua comparando LightGBM e padrão semanal em janela cronológica recente. Essa janela também seleciona o método e não é tratada como validação externa. O cenário Studio mostrou uma série em que a referência semanal venceu, evitando presumir superioridade do modelo.
- Entregues manual completo, roteiro e seis slides com duração prevista de 4min30s. “Empresa” é apresentada como proposta de solução/projeto, sem inventar registro formal, clientes, faturamento ou resultados comerciais.
- Os materiais ficam em `outputs/looniemind-v11-20261027/` e podem ser baixados por rotas com lista fixa de arquivos, acessíveis na Exportação. A base pode ser regenerada com `python -m scripts.generate_dataset --end 2026-10-27`. Não houve envio ao GitHub ou publicação externa nesta atualização.
