# Roteiro oral do primeiro checkpoint

Tempo-alvo: **6min30s**, incluindo a passagem rápida pelas referências. Margem até o limite de 7 min: 30 s. Perguntas: 3 min adicionais, conforme o e-mail. Ensaiar com cronômetro e ajustar as falas ao ritmo do grupo.

## Slide 1 — Tema (0:00–0:25)

“Nosso projeto se chama Quanto custa a abstração? Vamos estudar o custo de containers Docker e do monitoramento de arquivos no Linux. Este primeiro checkpoint apresenta a fundamentação e a proposta metodológica. A implementação dos benchmarks em C está em andamento.”

## Slide 2 — Motivação e literatura (0:25–1:20)

“Containers ajudam a organizar a execução de aplicações, e monitores permitem reagir a alterações em arquivos. Queremos entender o custo desses recursos. Felter e colegas mostram que o desempenho depende da carga e chamam atenção para I/O. A documentação do kernel e do Docker explica por que o caminho de armazenamento merece uma comparação própria. Já o manual do inotify mostra que a fila pode transbordar e que notificações podem ser agrupadas. Isso exige cuidado para interpretar eventos não detectados. Os trabalhos de Mytkowicz e de Georges orientam o controle dos experimentos e o tratamento da variabilidade.”

## Slide 3 — Perguntas e hipóteses (1:20–2:10)

“Temos três perguntas: quanto Docker altera operações básicas, como polling e inotify se comportam sob carga e se o armazenamento do container altera esse comportamento. Esperamos baixo overhead em algumas operações de CPU e memória. Para inotify, esperamos menor CPU e menor latência que polling, mas com risco de overflow. Também esperamos diferenças entre configurações de armazenamento. Essas são hipóteses anteriores à coleta. Compartilhar o kernel não garante que todos os custos sejam iguais.”

## Slide 4 — Parte A (2:10–2:55)

“Na Parte A, executaremos os mesmos micro-benchmarks em C diretamente no Linux e dentro do Docker. O plano inclui syscall, fork com wait, troca de bytes por pipe, I/O e alocação de memória. Vamos medir tempo por operação ou throughput. Os cuidados incluem manter as flags de compilação e declarar o tratamento de cache e sincronização de disco. O teste por pipe inclui comunicação e escalonamento. Ele não isola um custo puro de troca de contexto.”

## Slide 5 — Partes B e C (2:55–3:50)

“No monitoramento, o gerador realizará operações com taxas crescentes e registrará um log de referência. Polling terá intervalos de 50 milissegundos e um segundo, e será comparado com inotify. O mesmo desenho será repetido em execução nativa e nos containers com overlay, bind mount e volume. Vamos medir CPU, latência e operações não observadas. A taxa realmente alcançada também será medida, porque a taxa configurada pode exceder a capacidade da máquina.”

## Slide 6 — Confiabilidade (3:50–4:50)

“O ponto central é saber se uma operação foi observada. Vamos separar séries de criação, modificação e remoção e usar caminhos únicos, com os arquivos necessários preparados antes da rodada. Isso ajuda a associar operações e detecções sem confundir várias notificações com várias operações. A latência será calculada só para pares válidos e apresentada junto da cobertura. O overflow será registrado separadamente. Gerador e monitor usarão relógio monotônico na mesma instância Linux, e o monitor deverá estar pronto antes da carga.”

## Slide 7 — Protocolo e análise (4:50–5:45)

“Começaremos por um piloto para validar os componentes. Propomos rodadas de 30 segundos, uma rodada de aquecimento e pelo menos dez rodadas válidas por condição, em ordem aleatória por bloco. A análise apresentará média, desvio padrão e intervalo de confiança entre rodadas, além de mediana e p95 da latência. Não vamos retirar resultados apenas por serem ruins. Caso seja preciso usar uma VM, tanto o cenário direto quanto o Docker deverão executar na mesma VM Linux, e isso será declarado.”

## Slide 8 — Evolução e próximos passos (5:45–6:20)

“Neste checkpoint, apresentamos as perguntas, as hipóteses e a proposta de medição fundamentada em seis fontes. A parte em C está em desenvolvimento, e ainda não apresentamos resultados experimentais. O próximo passo é integrar os componentes e concluir o piloto. Depois, faremos a coleta e confrontaremos os resultados com as hipóteses. A entrega final está planejada para 26 de novembro.”

## Slide 9 — Referências (6:20–6:30)

“Estas são as seis referências usadas na proposta. A bibliografia completa e os links estão no relatório. Obrigado.”

## Divisão sugerida de fala

| Integrante | Slides | Tempo aproximado |
|---|---|---|
| P1 ou abertura escolhida pelo grupo | 1–3 | 2min10s |
| P2 | 4 | 45s |
| P3 | 5–6 | 1min55s |
| P4 | 7–9 | 1min40s |

A divisão acompanha os temas e não busca igualdade exata de tempo. Se a troca de apresentadores atrasar, retirar exemplos das falas, mantendo as perguntas, métricas e situação real do projeto.

## Respostas para possíveis perguntas

**Por que unir containers e monitoramento?** A Parte C conecta os temas: o mesmo monitor será avaliado em diferentes formas de armazenamento do container.

**Já há implementação ou resultados?** A implementação em C está em desenvolvimento. Não apresentamos resultados experimentais neste checkpoint.

**Por que usar Python nos monitores?** Para comparar dois mecanismos com a mesma linguagem e interface. O custo da implementação Python fará parte da medição. A versão em C do inotify é opcional e permitiria investigar o custo da linguagem.

**Uma notificação ausente significa bug?** Não necessariamente. Polling pode deixar de observar estados intermediários e inotify pode agrupar notificações. Por isso usaremos correspondência controlada e registraremos overflow separadamente.

**Por que dez repetições?** É o mínimo definido no projeto, não uma garantia automática de precisão. O piloto e a largura dos intervalos de confiança indicarão a necessidade de ampliar a coleta.

**Docker compartilha o kernel. Por que teria overhead?** Compartilhar o kernel reduz algumas camadas, mas não elimina os efeitos da configuração de isolamento, recursos e armazenamento. O experimento básico estima o efeito conjunto, sem atribuí-lo a um único mecanismo.

**O que ainda falta definir?** Máquina Linux, versões exatas e detalhes ajustados no piloto. Esses itens devem ficar fixados antes da coleta principal.

## Antes da entrega

- Preencher nomes e matrículas no relatório e nos slides.
- Publicar os slides na plataforma escolhida e inserir seu link no relatório.
- Revisar com P2 se a descrição coincide com o que está em desenvolvimento.
- Confirmar o formato de submissão do GitHub exigido pelo professor.
- Ensaiar em até 6min30s e testar a abertura da apresentação.
- Revisar criticamente o material e a bibliografia. Registrar o uso de IA conforme as regras da disciplina.
