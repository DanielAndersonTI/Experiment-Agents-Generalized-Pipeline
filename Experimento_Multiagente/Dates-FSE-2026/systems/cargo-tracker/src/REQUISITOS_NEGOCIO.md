# Requisitos da Aplicacao Cargo Tracker

Levantamento elaborado a partir do comportamento implementado no codigo-fonte da aplicacao, com foco em regras de negocio e expectativas operacionais, evitando detalhamento excessivamente tecnico.

## Requisitos funcionais

### 1. Cadastro e abertura da carga

- `RF01` O sistema deve permitir registrar uma nova carga informando origem, destino e prazo limite de chegada.
- `RF02` Cada carga cadastrada deve receber um identificador unico de rastreamento.
- `RF03` A origem e o destino da carga devem ser diferentes.
- `RF04` A origem da carga deve permanecer fixa durante todo o ciclo logistico.
- `RF05` O cadastro da carga pode ser concluido mesmo antes da definicao da rota.
- `RF06` O prazo de chegada deve ser obrigatorio e deve servir como criterio para o planejamento da viagem.
- `RF07` O sistema deve permitir selecionar origem e destino apenas entre localidades logisticas previamente cadastradas.

### 2. Planejamento e roteirizacao

- `RF08` O sistema deve consultar e apresentar rotas candidatas compativeis com a necessidade da carga.
- `RF09` Uma rota candidata so deve ser considerada valida quando respeitar a origem, o destino final e o prazo de chegada da carga.
- `RF10` O usuario deve poder escolher uma das rotas apresentadas e vincula-la a carga.
- `RF11` Quando a carga ainda nao tiver rota definida, ela deve permanecer identificada como "nao roteirizada".
- `RF12` Quando nenhuma rota atender aos criterios informados, o sistema deve informar que nao ha opcao viavel para a especificacao atual.
- `RF13` O sistema deve exibir os trechos da rota escolhida, incluindo pontos de embarque, desembarque, viagem e datas previstas.

### 3. Replanejamento da viagem

- `RF14` O sistema deve permitir alterar o destino de uma carga ja cadastrada.
- `RF15` O novo destino nao pode ser igual nem a origem nem ao destino atual da carga.
- `RF16` Ao alterar o destino, o sistema deve reavaliar a rota atual da carga.
- `RF17` Quando a rota atual deixar de atender ao novo destino, a carga deve passar a exigir nova roteirizacao.
- `RF18` O sistema deve permitir replanejar a rota de cargas que ficaram fora da rota prevista ou que tiveram o destino alterado.

### 4. Acompanhamento e rastreamento

- `RF19` O sistema deve permitir consultar uma carga pelo identificador de rastreamento.
- `RF20` Na consulta, o sistema deve apresentar a situacao atual da carga.
- `RF21` O sistema deve informar a ultima localizacao conhecida da carga.
- `RF22` O sistema deve informar a previsao de chegada quando a carga estiver com rota valida e em curso compativel com o planejamento.
- `RF23` O sistema deve informar a proxima etapa operacional esperada da carga sempre que essa previsao puder ser determinada.
- `RF24` O sistema deve manter e exibir o historico de eventos logisticos associados a carga.
- `RF25` O historico deve diferenciar eventos esperados de eventos fora do planejado.
- `RF26` O sistema deve sinalizar quando a carga estiver fora da rota esperada.
- `RF27` O sistema deve permitir visualizar a carga com apoio geografico, destacando origem, destino final e ultima localizacao conhecida.

### 5. Gestao operacional das cargas

- `RF28` O sistema deve disponibilizar uma visao administrativa consolidada das cargas.
- `RF29` As cargas devem ser agrupadas, no minimo, nas categorias "nao roteirizadas", "roteirizadas em andamento" e "retiradas pelo destinatario".
- `RF30` O sistema deve permitir abrir o detalhamento de qualquer carga a partir da visao administrativa.
- `RF31` Cargas roteirizadas e ainda nao retiradas devem poder ser acompanhadas como cargas em transito.

### 6. Registro de eventos logisticos

- `RF32` O sistema deve permitir registrar eventos logisticos dos tipos: recebimento, embarque, desembarque, alfandega e retirada.
- `RF33` Todo evento logistico deve estar associado a uma carga existente.
- `RF34` Todo evento logistico deve informar a localidade em que ocorreu e a data de ocorrencia.
- `RF35` Eventos de embarque e desembarque devem estar associados a viagem correspondente.
- `RF36` Eventos que nao sejam de embarque ou desembarque nao devem exigir identificacao de viagem.
- `RF37` O sistema deve rejeitar tentativas de registro com carga, localidade ou viagem inexistentes.
- `RF38` O registro de um evento valido deve atualizar a situacao operacional da carga.
- `RF39` Apos cada evento valido, o sistema deve recalcular informacoes como status de transporte, localizacao conhecida, proxima etapa esperada e aderencia ao plano.
- `RF40` Quando um evento indicar execucao diferente da rota prevista, a carga deve ser marcada como fora de rota.
- `RF41` Quando a carga for descarregada no destino final, o sistema deve marca-la como chegada ao destino.
- `RF42` Quando a retirada pelo destinatario for registrada, a carga deve ser considerada concluida do ponto de vista logistico.

### 7. Canais de operacao e monitoramento

- `RF43` O sistema deve permitir o registro de eventos logisticos por mais de um canal operacional.
- `RF44` Entre os canais suportados, deve haver pelo menos interface operacional, servico de integracao e processamento de arquivos de entrada.
- `RF45` O sistema deve disponibilizar uma visao consolidada das cargas para consumo por canais de monitoramento.
- `RF46` O sistema deve manter os canais de acompanhamento alinhados com a situacao mais recente de cada carga.

## Requisitos nao funcionais

### 1. Integridade e consistencia do negocio

- `RNF01` O sistema deve preservar a consistencia entre cadastro da carga, rota planejada e eventos realizados.
- `RNF02` Nenhum evento invalido pode alterar o estado da carga.
- `RNF03` As regras de origem, destino, prazo e compatibilidade da rota devem ser aplicadas de forma uniforme em todos os canais de operacao.
- `RNF04` A situacao da carga deve ser recalculada sempre que houver mudanca relevante de planejamento ou execucao.

### 2. Rastreabilidade e auditoria operacional

- `RNF05` O sistema deve manter historico suficiente para reconstituir o ciclo logistico da carga.
- `RNF06` Cada evento deve conservar, no minimo, o momento em que ocorreu e o momento em que foi registrado no sistema.
- `RNF07` Tentativas rejeitadas de registro devem ser identificaveis para posterior analise operacional.
- `RNF08` O sistema deve permitir distinguir cargas entregues corretamente, cargas ainda em transito e cargas com desvio operacional.

### 3. Atualizacao e tempestividade

- `RNF09` A atualizacao da situacao da carga deve ocorrer em tempo adequado ao acompanhamento operacional.
- `RNF10` O recebimento de eventos deve continuar fluindo mesmo quando o recalculo detalhado da situacao ocorrer em segundo plano.
- `RNF11` Entradas recebidas por arquivo devem ser processadas de forma periodica, sem depender de acionamento manual constante.
- `RNF12` Os canais de monitoramento devem refletir a informacao mais recente disponivel sobre a carga.

### 4. Usabilidade operacional

- `RNF13` As informacoes apresentadas ao usuario devem ser organizadas por situacao de negocio, e nao apenas por estrutura tecnica.
- `RNF14` A navegacao operacional deve facilitar tarefas frequentes, como localizar carga, consultar detalhes, escolher rota e registrar evento.
- `RNF15` O sistema deve reduzir erros de operacao por meio de listas controladas de localidades, viagens, tipos de evento e identificadores de carga.
- `RNF16` Mensagens de erro e ausencia de rota devem ser compreensiveis para uso administrativo e logistico.

### 5. Resiliencia do processamento

- `RNF17` Falhas em uma tentativa isolada de registro nao devem comprometer o processamento das demais cargas.
- `RNF18` Registros recebidos em formato invalido devem ser separados para tratamento posterior, sem interromper o restante da carga de trabalho.
- `RNF19` O sistema deve tratar cargas fora da rota como excecoes operacionais visiveis, para permitir acao corretiva rapida.

### 6. Interoperabilidade entre canais

- `RNF20` O sistema deve manter coerencia entre os dados apresentados na interface administrativa, no rastreamento, nos canais moveis e nas integracoes.
- `RNF21` As informacoes principais da carga devem poder ser trocadas em formatos padronizados para facilitar integracao com outros sistemas.
- `RNF22` O modelo de acompanhamento deve ser unico, independentemente do canal usado para registrar ou consultar a carga.

## Observacoes de escopo inferido

- O codigo analisado concentra-se em cadastro, roteirizacao, acompanhamento e registro operacional de eventos da carga.
- Nao foram identificadas, como parte central do escopo atual, regras de cobranca, faturamento, gestao contratual ou controle de acesso por perfil.
