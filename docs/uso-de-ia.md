# Uso de IA generativa

## Primeiro checkpoint — 4 de novembro de 2026

O grupo utilizou o Codex, da OpenAI, para auxiliar a pesquisa de referências na internet, a elaboração de uma versão inicial do relatório técnico, a organização dos slides e o roteiro de apresentação. A ferramenta consultou o template disponível no repositório e fontes acadêmicas e técnicas identificadas na bibliografia. Também auxiliou na explicitação de limitações metodológicas, incluindo agrupamento de notificações, correspondência de eventos e comparação em ambiente virtualizado.

Não foram gerados resultados experimentais nem realizadas medições para esta entrega. O estado da implementação em C foi informado pelo integrante do grupo. Parâmetros de experimentos e cronograma intermediário são propostas a validar.

**TODO do grupo:** revisar afirmações e referências, adequar o protocolo aos componentes implementados, confirmar as regras institucionais aplicáveis e registrar as revisões humanas realizadas. Os integrantes são responsáveis pelo conteúdo submetido e por sua explicação na apresentação.

## Coleta exploratória — 17 de novembro de 2026

O Codex auxiliou a executar os componentes existentes em containers Linux no
Docker Desktop, coletar os CSVs e criar scripts simples de resumo estatístico.
Também auxiliou a criar os alvos de automação para Linux nativo, Docker no
Linux e comparação das médias, além das verificações que impedem executar um
alvo com o sistema operacional errado.
Também ajudou a documentar as limitações da medição no macOS: o container roda
em uma VM Linux, o teste de disco usa `overlayfs` e a demonstração dos monitores
ainda não possui um log-oráculo. Os números publicados foram produzidos pela
execução real dos programas no Mac do integrante e devem ser revisados pelo
grupo antes da apresentação; nenhum resultado foi inventado ou preenchido
manualmente.
