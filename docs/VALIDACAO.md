# Validação da entrega local

## Pacote e apresentação atuais · 28/10/2026

**41 testes passaram em 65,06 s**, incluindo o download da apresentação de oito slides, do roteiro correspondente e do pacote completo pela API. Ruff sem erros, quatro módulos JavaScript com sintaxe válida e `pip check` sem dependências quebradas. Permanecem três avisos de depreciação das bibliotecas de teste e leitura de XLS, sem falha nos testes.

O pacote `outputs/looniemind-v11-20261027/LoonieMind_Materiais_Completos.zip` reúne somente a apresentação atual: oito slides com notas de fala, duração planejada de 4min35s e encerramento sobre o valor da solução. Inclui manual, três planilhas, base sintética, roteiro em Markdown/PDF e documentação. O novo roteiro tem quatro páginas, todas renderizadas e inspecionadas, e 470 palavras de fala. As apresentações anteriores permanecem no repositório como histórico.

A apresentação atual conserva duas tabelas editáveis, um gráfico e a planilha de dados incorporada. Sua conferência de estrutura, fontes e importação pelo editor passou; o comprovante está em [apresentacao-8-slides.json](relatorios/apresentacao-8-slides.json). Não foi feita abertura nativa no Microsoft PowerPoint.

O empacotamento confere os hashes dos CSVs com o manifesto da base e registra hashes SHA-256 de todos os materiais em `MANIFESTO-PACOTE.json`, dentro do ZIP. O comprovante externo é `outputs/looniemind-v11-20261027/Manifesto_Materiais_Atuais.json`. Para conferir conteúdo e integridade contra os arquivos atuais, execute `python -m scripts.package_materials --check`.

Os candidatos à publicação foram conferidos sem achados nos padrões de credenciais examinados. O banco operacional, modelos locais, ambiente virtual e arquivos temporários estão fora do Git. O banco histórico `Database/LoonieMind.db` continua idêntico ao arquivo original do repositório. Os registros abaixo descrevem as entregas anteriores.

## Atualização 1.1 · 27/10/2026

**40 testes passaram**, com Ruff sem erros e sintaxe JavaScript conferida. A última execução completa levou 57,47 s. A suíte passou a cobrir os oito campos complementares, importação/exportação/reimportação, preservação de metadados em edições, entrada vazia separada dos exemplos, saldo diário conciliado e migração v1 → v2 com snapshot. A reimportação preserva o tipo pendente em vez de rejeitar o próprio CSV exportado.

A base v2 contém 14.400 exemplos de classificação, 12 classes e 288 famílias. Treino/validação/teste: 9.600/2.400/2.400 exemplos e 192/48/48 famílias disjuntas. F1 macro: 0,6034 na validação e 0,6766 no teste. O modelo foi reajustado sobre toda a base depois da avaliação. Métricas e resultados por classe em [avaliacao-v1.1.json](relatorios/avaliacao-v1.1.json). A base financeira contém 10.965 registros em três cenários, com manifesto e hashes em `datasets/sintetica-v2/`.

Os relatórios têm fórmulas verificadas e foram renderizados por aba. O PowerPoint tem seis slides, notas com roteiro de 4min30s, tabela e gráfico editáveis. A validação de estrutura, dimensões, fontes, incorporação de dados e importação pelo editor passou. As seis imagens dos slides foram inspecionadas; isso não significa que o arquivo foi aberto no Microsoft PowerPoint. O manual de oito páginas e o roteiro de três páginas foram renderizados e revisados.

O dashboard foi verificado com os dados ampliados, distinguindo saldo consolidado de resultado do período. A demonstração anterior foi preservada. Os resultados abaixo permanecem como registro histórico da versão 1.0, não como métricas atuais.

## Registro histórico da versão 1.0

Data: 27/10/2026. Ambiente: Windows x64, Python 3.12.1. Dependências fixadas nos arquivos `requirements-lock.txt` e `requirements-dev-lock.txt`.

Resultado final: **35 testes passaram**, Ruff sem erros, quatro módulos JavaScript com sintaxe válida e `pip check` sem dependências quebradas. A execução final da suíte levou 13,93 segundos; os avisos de bibliotecas estão descritos abaixo.

O classificador demonstrativo entregue foi treinado com 576 exemplos sintéticos, 12 classes, 432 exemplos no treino e 144 no teste por grupos. O F1 macro observado foi **0,5569**, versão `6d1f1c873850`. Esse resultado limitado reforça a necessidade de revisão humana e de uma base real representativa; não foi apresentado como qualidade de produção. Relatório por classe e versões de bibliotecas ficam nos metadados locais do modelo.

## Verificações automatizadas

A suíte cobre domínio financeiro e API em bancos temporários independentes:

- Precisão em centavos, valores brasileiros/decimais, formato ambíguo, sinais e rejeição de valores inválidos.
- Criação/isolamento entre empresas, saldo inicial e data de referência, correções e auditoria.
- Validação de entradas, datas futuras e representação inteira de dinheiro.
- Upload, prévia sem gravação, mapeamento, seleção de abas, CSV UTF-8/CP1252, XLS e XLSX.
- Confirmação idempotente, bloqueio de mesma aba, preservação de transações legítimas iguais e consentimento para semelhantes.
- Importação parcial explícita, exclusão de tipo desconhecido dos totais e rollback de todas as linhas quando uma escrita falha.
- Exportação CSV/XLSX com filtros, centavos conciliados e textos tratados para evitar interpretação como fórmulas.
- Snapshot de backup, integridade, restauração em pasta nova sem sobrescrita e rejeição de caminhos fora do escopo.
- Restauração dos arquivos originais, reabertura da aplicação restaurada e conclusão de uma prévia preservada.
- Treino demonstrativo, separação de dados, preservação de revisão humana, previsão recursiva e atualização após mudança de saldo.
- Histórico insuficiente/desatualizado, ausência de artefato e separação dos modelos por empresa.
- Restrição de Host e recusa de escritas de outra origem.

Também executados: análise estática Python (Ruff), compilação dos módulos, validação sintática dos módulos JavaScript e `pip check` para consistência de dependências. Os resultados da execução final são registrados no resumo da entrega. Avisos de depreciação de bibliotecas de teste/leitura de XLS não impedem o funcionamento nas versões fixadas.

Comandos de reprodução:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev-lock.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check looniemind scripts tests run.py
.\.venv\Scripts\python.exe -m pip check
node --check web/app.js
node --check web/charts.js
node --check web/icons.js
node --check web/api-reference.js
```

## Verificações no navegador

Foi utilizada uma base separada em `.pytest_cache/browserdata`, servida em outra porta. Esses registros não foram inseridos na demonstração entregue em `data/`.

| Cenário | Resultado observado |
|---|---|
| Cadastro pela tela | Empresa “Validação da interface”, saldo inicial R$ 5.000,00. |
| Lançamento manual | Despesa R$ 25,50; dashboard atualizado para R$ 4.974,50. |
| Edição | Despesa alterada para R$ 30,50 e revisão confirmada. |
| Modelo de CSV | Arquivo gerado pela aplicação, baixado e enviado pelo seletor de arquivos. |
| Prévia | 4 linhas válidas, 0 inválidas, 0 sem tipo; confirmação habilitada. |
| Confirmação | 4 lançamentos importados; mensagem de conclusão e acesso à revisão. |
| Sugestão sem modelo | Categoria Fornecedores por palavra-chave, sem falsa probabilidade de IA. |
| Revisão | Sugestão confirmada; lista de pendências ficou vazia. |
| Conciliação | Saldo final R$ 5.998,10 = 5.000,00 − 30,50 + 1.500,00 + 650,00 − 800,50 − 320,90. |
| Busca global | Termo “validação” retornou somente o lançamento esperado. |
| Console no fluxo testado | Nenhum erro registrado. |
| Previsão da demonstração | 210 dias de histórico; 30 dias futuros, método e MAE apresentados. |
| Persistência | Demonstração preservada após reiniciar o servidor local. |
| Responsividade | Desktop com 1440 px e tela com 390 px; menu móvel navegável e sem transbordamento horizontal do documento. |
| Segunda empresa | Iniciou com saldo zero e histórico vazio; a empresa anterior manteve saldo R$ 5.998,10 e 5 movimentações. |
| Exportação na interface | Alternância entre lançamentos/previsão exibiu os filtros/horizonte correspondentes. Arquivos CSV/XLSX também foram verificados pela suíte da API. |
| Referência da API | 28 seções de documentação/esquemas carregadas localmente, sem erros no console. |

A [referência visual original](01-prototipacao/referencia-interface.jpeg) e a [captura do dashboard implementado](01-prototipacao/dashboard-v1.jpg) registram a evolução da interface.

## Alcance da validação

Foram testados dados sintéticos e arquivos gerados para os testes; não foram disponibilizados dados reais de empresa. As métricas do classificador demonstrativo são internas à base sintética. Validação externa, avaliação do professor e testes com planilhas reais ainda dependem desses insumos.

Não foram validados instaladores nativos ou hospedagem multiusuário. A rotina de CI está configurada para Windows/Linux, mas o resultado de uma execução no GitHub não é presumido por existir o arquivo de configuração. O banco original `Database/LoonieMind.db` foi conferido por hash e preservado.
