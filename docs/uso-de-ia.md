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

## Atualização para o seminário — 23 de novembro de 2026

O Codex auxiliou a adaptar o README ao template do professor, preservando o
checkpoint 1 como registro histórico, e a verificar as seis fontes já utilizadas.
Executou os cinco benchmarks C no Docker Desktop, com uma rodada de aquecimento
e dez válidas, além de dez rodadas válidas dos monitores Docker e do polling
nativo no macOS. A tentativa C nativa e a recusa do alvo Linux foram documentadas;
não foram apresentados resultados nativos Linux inexistentes nesta máquina.

Foram resolvidos conflitos de merge em três arquivos dos benchmarks, mantendo
os trechos `lowlevel`, e corrigida a automação para recompilar os executáveis no
container. A IA auxiliou a escrever os scripts de repetição do polling e de
consolidação dos resultados, as tabelas, o gráfico vetorial e as instruções de
reprodução. Os CSVs Linux do integrante foram analisados separadamente da coleta
ARM64 do Mac; diferenças de kernel e configuração de CPU foram explicitadas.

A afirmação de overhead geral de 2% a 5% não foi adotada como conclusão: a análise
usa os números dos CSVs, sem ajustá-los a essa expectativa. CPU, latência com
oráculo e comparação controlada das montagens continuam identificadas como
pendências. Cabe ao grupo revisar o texto, preencher integrantes e slides,
validar a interpretação e explicar os programas e as limitações na apresentação.
