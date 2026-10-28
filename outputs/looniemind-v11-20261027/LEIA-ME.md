# Materiais atualizados do LoonieMind · versão 1.1

- PowerPoint: `LoonieMind_Empresa_e_Sistema_8_Slides.pptx`, oito slides com notas de fala e duração planejada de 4min35s. Apresenta empresa, público, desafio, sistema, classificação, previsão, modelo de negócio proposto e valor para o empreendedor.
- Manual: funcionamento do sistema, planilhas, regras financeiras, treinamento, previsão e limites.
- Roteiro: `Roteiro_8_Slides.pdf` e `Roteiro_8_Slides.md`, com as falas e os tempos dos oito slides.
- Modelo de importação: aba Movimentacoes vazia, exemplos fictícios separados e orientações.
- Relatório: 4.124 lançamentos fictícios da Aurora, com resumo e análises.
- Projeção: 30 dias, saldo diário e métodos/erros de validação.
- datasets/sintetica-v2: 14.400 exemplos rotulados e 10.965 movimentos em três cenários, com manifesto/hashes.
- docs/: manuais em texto, arquitetura, decisões, validação e evidências da IA e da apresentação.
- MANIFESTO-PACOTE.json: lista dos arquivos e seus hashes SHA-256 para conferir a integridade.

Os dados são artificiais. As métricas demonstram a avaliação nessa base, sem comprovar desempenho em empresas reais.
A aplicação completa está em https://github.com/GabrielIzi/LoonieMind. Baixe ou clone o repositório e abra `Iniciar LoonieMind.cmd` com Python 3.12 instalado. Este ZIP reúne os materiais para utilização, demonstração e treinamento, sem o banco operacional do computador.
Os relatórios exportados não alteram automaticamente o sistema; confira a aba e as duplicidades ao reimportar.

O pacote contém somente a apresentação atual. As versões anteriores foram preservadas no repositório como histórico. O último slide atual destaca o valor para o empreendedor; os preços dos planos são propostas comerciais, sem cobrança implementada.

Para reconstruir os materiais a partir dos arquivos do repositório: `python -m scripts.package_materials`. Para apenas conferir: `python -m scripts.package_materials --check`.
