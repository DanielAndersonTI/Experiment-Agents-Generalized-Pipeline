# Documento de Requisitos de Negocio

## 1. Objetivo

Este documento formaliza os requisitos funcionais e nao funcionais da aplicacao DayTrader7 com base na analise do codigo-fonte disponivel no repositorio. O foco do documento esta nas regras de negocio percebidas na aplicacao, com linguagem orientada ao funcionamento do sistema e ao valor entregue aos seus usuarios.

## 2. Escopo

A aplicacao tem como objetivo simular a operacao de uma corretora de investimentos, permitindo que investidores cadastrem contas, consultem o mercado, acompanhem suas carteiras e realizem operacoes de compra e venda de ativos.

Este documento considera os fluxos centrais do negocio observados no codigo da aplicacao, especialmente:

1. Cadastro e autenticacao de investidores.
2. Gestao de conta e perfil.
3. Consulta de mercado e cotacoes.
4. Negociacao de ativos.
5. Acompanhamento de carteira e desempenho.
6. Administracao operacional da simulacao.

Nao fazem parte do escopo principal deste documento as paginas e rotinas de teste tecnico, validacao de infraestrutura e cargas de benchmark que nao representam regras centrais do negocio.

## 3. Perfis Considerados

### 3.1 Investidor

Usuario responsavel por acessar sua conta, consultar o mercado, negociar ativos e acompanhar sua carteira.

### 3.2 Administrador da Simulacao

Usuario responsavel por preparar, reinicializar e configurar o ambiente operacional da simulacao.

## 4. Requisitos Funcionais

### 4.1 Cadastro e Acesso

**RF01.** O sistema deve permitir o cadastro de novos investidores.

**RF02.** O cadastro do investidor deve contemplar, no minimo, identificacao do usuario, senha, confirmacao de senha, nome completo, endereco, e-mail, cartao e saldo inicial de abertura.

**RF03.** O sistema deve validar se a senha e a confirmacao de senha informadas no cadastro sao identicas.

**RF04.** O sistema nao deve permitir o cadastro de um investidor com identificacao ja existente.

**RF05.** O sistema deve autenticar o investidor por meio de usuario e senha.

**RF06.** O sistema deve permitir o inicio de sessao para investidores autenticados.

**RF07.** O sistema deve permitir o encerramento da sessao do investidor por meio de logout.

**RF08.** O sistema deve impedir o acesso aos recursos de conta, carteira e negociacao quando o investidor nao estiver autenticado.

### 4.2 Conta e Perfil do Investidor

**RF09.** O sistema deve manter uma conta individual para cada investidor cadastrado.

**RF10.** A conta do investidor deve registrar saldo atual, saldo inicial, data de criacao, data do ultimo acesso, total de logins e total de logouts.

**RF11.** O sistema deve permitir a consulta dos dados cadastrais e financeiros da conta do investidor.

**RF12.** O sistema deve permitir a atualizacao do perfil do investidor.

**RF13.** A atualizacao do perfil deve contemplar, no minimo, senha, nome completo, endereco, e-mail e cartao cadastrado.

**RF14.** O sistema deve exigir o preenchimento dos campos essenciais para efetivar a atualizacao do perfil.

**RF15.** O sistema deve impedir a atualizacao do perfil quando a senha e a confirmacao de senha forem divergentes.

### 4.3 Consulta de Mercado e Cotacoes

**RF16.** O sistema deve permitir a consulta de cotacoes de ativos a partir de seus codigos.

**RF17.** O sistema deve permitir a consulta simultanea de mais de um ativo.

**RF18.** Para cada ativo consultado, o sistema deve apresentar informacoes como nome da empresa, volume negociado, faixa de preco, preco de abertura, preco atual e variacao.

**RF19.** O sistema deve disponibilizar um resumo consolidado do mercado.

**RF20.** O resumo consolidado do mercado deve apresentar, no minimo, indice geral de desempenho, indice de abertura, volume negociado, ativos com maiores altas e ativos com maiores baixas.

**RF21.** O sistema deve tratar codigos de ativos invalidos sem interromper a navegacao do investidor.

### 4.4 Negociacao de Ativos

**RF22.** O sistema deve permitir a compra de ativos pelo investidor mediante informacao do codigo do ativo e da quantidade desejada.

**RF23.** O sistema deve permitir a venda de ativos ja existentes na carteira do investidor.

**RF24.** Toda operacao de compra ou venda deve gerar uma ordem individual de negociacao.

**RF25.** Toda ordem deve possuir identificacao propria, tipo, quantidade, preco, data de abertura, data de conclusao, status e taxa da operacao.

**RF26.** O sistema deve aplicar taxa fixa de operacao nas ordens de compra e venda.

**RF27.** Em operacoes de compra, o sistema deve debitar do saldo do investidor o valor correspondente ao ativo negociado acrescido da taxa da operacao.

**RF28.** Em operacoes de venda, o sistema deve creditar ao saldo do investidor o valor liquido da operacao, considerando o desconto da taxa aplicavel.

**RF29.** O sistema deve permitir que as ordens sejam processadas de forma imediata ou posterior, conforme a configuracao operacional da simulacao.

**RF30.** O sistema deve registrar o andamento da ordem por meio de status de negocio, contemplando pelo menos os estados aberta, em processamento, concluida e cancelada.

**RF31.** O sistema nao deve permitir a conclusao repetida de uma mesma ordem.

**RF32.** O sistema deve cancelar a venda quando a posicao informada ja tiver sido negociada anteriormente ou nao estiver mais disponivel.

**RF33.** O sistema deve apresentar ao investidor a confirmacao do envio da ordem para processamento.

### 4.5 Carteira e Acompanhamento do Investidor

**RF34.** O sistema deve manter a carteira do investidor com as posicoes decorrentes de compras realizadas.

**RF35.** Quando uma ordem de compra for concluida, o sistema deve registrar a nova posicao na carteira do investidor.

**RF36.** Quando uma ordem de venda for concluida, o sistema deve remover da carteira a posicao correspondente.

**RF37.** O sistema deve permitir a consulta da carteira do investidor.

**RF38.** Para cada posicao da carteira, o sistema deve apresentar, no minimo, identificacao da posicao, data da compra, ativo, quantidade, preco de compra, preco atual, valor aplicado, valor de mercado e ganho ou perda.

**RF39.** O sistema deve informar quando a carteira do investidor estiver vazia.

**RF40.** O sistema deve permitir a venda de uma posicao diretamente a partir da carteira.

**RF41.** O sistema deve calcular o valor total investido na carteira, o valor de mercado atual e o ganho ou perda consolidado.

**RF42.** O sistema deve apresentar ao investidor um resumo consolidado de sua posicao financeira, incluindo saldo em caixa, quantidade de posicoes, valor de mercado da carteira e resultado acumulado em relacao ao saldo inicial.

### 4.6 Historico e Alertas de Ordens

**RF43.** O sistema deve manter historico das ordens associadas ao investidor.

**RF44.** O sistema deve exibir uma visao resumida das ordens mais recentes do investidor.

**RF45.** O sistema deve permitir a consulta ampliada do historico de ordens.

**RF46.** O sistema deve alertar o investidor sobre ordens concluidas que ainda nao tenham sido apresentadas a ele.

**RF47.** A apresentacao do alerta deve informar, no minimo, identificacao da ordem, status, datas relevantes, tipo, ativo, quantidade e taxa aplicada.

### 4.7 Atualizacao de Informacoes de Mercado

**RF48.** O sistema deve atualizar o volume negociado e os indicadores de mercado dos ativos apos operacoes de compra e venda.

**RF49.** O sistema deve refletir essas atualizacoes nas consultas posteriores de cotacao e no resumo consolidado do mercado.

### 4.8 Administracao Operacional da Simulacao

**RF50.** O sistema deve permitir a configuracao de parametros operacionais da simulacao.

**RF51.** Entre os parametros operacionais, o sistema deve permitir definir o modo de processamento das ordens, a quantidade maxima de usuarios simulados, a quantidade maxima de ativos simulados e o intervalo de atualizacao do resumo do mercado.

**RF52.** O sistema deve permitir habilitar ou desabilitar alertas de ordens concluidas.

**RF53.** O sistema deve permitir preparar ou reconstruir a base de dados da simulacao.

**RF54.** O sistema deve permitir reinicializar os dados operacionais da simulacao.

**RF55.** Ao reinicializar os dados, o sistema deve disponibilizar estatisticas resumidas da execucao, incluindo usuarios, ativos, ordens, cancelamentos e posicoes existentes.

## 5. Requisitos Nao Funcionais

### 5.1 Seguranca e Controle de Acesso

**RNF01.** O sistema deve exigir autenticacao previa para acesso aos recursos restritos do investidor.

**RNF02.** O sistema deve garantir que as operacoes executadas durante a sessao sejam associadas ao investidor autenticado.

**RNF03.** O sistema deve encerrar adequadamente a sessao do investidor no logout, reduzindo o risco de uso indevido posterior.

### 5.2 Confiabilidade e Integridade do Negocio

**RNF04.** O sistema deve preservar a consistencia entre saldo, ordens, cotacoes e carteira apos cada operacao.

**RNF05.** O sistema deve manter rastreabilidade minima do ciclo de vida das ordens por meio de identificacao, datas e status.

**RNF06.** O sistema deve tratar falhas de processamento sem comprometer a integridade dos dados do investidor.

**RNF07.** O sistema deve impedir, sempre que possivel, duplicidade de conclusao ou reaproveitamento indevido de ordens e posicoes.

### 5.3 Desempenho e Capacidade Operacional

**RNF08.** O sistema deve suportar processamento imediato ou posterior de ordens, de modo a atender diferentes estrategias operacionais da simulacao.

**RNF09.** O sistema deve permitir o uso de atualizacao configuravel do resumo de mercado para equilibrar atualidade da informacao e custo operacional.

**RNF10.** O sistema deve suportar operacao com volumes elevados de usuarios, ativos e ordens simuladas.

### 5.4 Usabilidade e Experiencia de Uso

**RNF11.** O sistema deve apresentar ao investidor informacoes de negocio de forma clara, objetiva e organizada por contexto de uso.

**RNF12.** O sistema deve oferecer mensagens compreensiveis para situacoes como falha de login, erro de cadastro, divergencia de senha, dados obrigatorios ausentes e operacoes invalidas.

**RNF13.** O sistema deve permitir navegacao simples entre as visoes principais de home, conta, carteira, cotacoes, ordens e resumo de mercado.

### 5.5 Operacao e Administracao

**RNF14.** O sistema deve disponibilizar mecanismos administrativos para preparacao, configuracao e reinicializacao controlada do ambiente de simulacao.

**RNF15.** O sistema deve disponibilizar indicadores resumidos da execucao para apoio ao acompanhamento operacional da simulacao.

## 6. Observacoes

1. Este documento foi elaborado exclusivamente a partir da analise do codigo-fonte do projeto e de seus fluxos implementados.
2. Os requisitos aqui descritos representam o comportamento observado na aplicacao, podendo demandar refinamento adicional caso existam regras de negocio externas nao refletidas no codigo atual.
3. As funcionalidades voltadas a testes tecnicos e benchmark foram tratadas como apoio operacional e nao como nucleo do negocio, salvo quando impactam diretamente a administracao da simulacao.
