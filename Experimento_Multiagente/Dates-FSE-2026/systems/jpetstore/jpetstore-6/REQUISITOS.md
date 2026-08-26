# Documento de Requisitos

## 1. Objetivo

Este documento apresenta os requisitos funcionais e não funcionais da aplicação JPetStore, identificados a partir da análise do código-fonte, das telas, do fluxo de navegação e dos comportamentos implementados. O foco do documento está nas regras de negócio observadas na aplicação, com linguagem menos técnica e mais voltada ao funcionamento esperado do sistema.

## 2. Escopo da Aplicação

A aplicação tem como objetivo permitir a comercialização de animais de estimação por meio de uma loja virtual. O sistema oferece navegação por catálogo, pesquisa de produtos, cadastro e autenticação de clientes, gerenciamento de carrinho de compras, realização de pedidos e consulta ao histórico de compras.

## 3. Perfis Envolvidos

- **Visitante:** usuário que navega pela loja sem estar autenticado.
- **Cliente:** usuário autenticado que pode manter cadastro, montar carrinho, concluir compras e consultar pedidos anteriores.

## 4. Requisitos Funcionais

### 4.1. Catálogo e Navegação

**RF01.** O sistema deve permitir que visitantes e clientes entrem na loja virtual e naveguem pelo catálogo principal.

**RF02.** O sistema deve organizar os produtos por categorias de animais, contemplando as categorias de peixes, cães, répteis, gatos e aves.

**RF03.** O sistema deve permitir o acesso às categorias por diferentes caminhos de navegação, como menu principal, atalhos rápidos e elementos visuais da página inicial.

**RF04.** O sistema deve permitir a visualização da lista de produtos de cada categoria.

**RF05.** O sistema deve permitir a visualização dos itens disponíveis de cada produto.

**RF06.** O sistema deve permitir a visualização do detalhamento de cada item, incluindo descrição, identificação, preço e situação de estoque.

### 4.2. Pesquisa de Produtos

**RF07.** O sistema deve permitir pesquisar produtos por palavra-chave.

**RF08.** A pesquisa deve considerar o nome do produto como base para retorno dos resultados.

**RF09.** Quando nenhuma palavra-chave for informada, o sistema deve impedir a pesquisa e orientar o usuário a preencher o campo de busca.

### 4.3. Cadastro, Acesso e Perfil do Cliente

**RF10.** O sistema deve permitir o cadastro de novos clientes por meio do preenchimento de dados de identificação, contato, endereço e credenciais de acesso.

**RF11.** O sistema deve permitir que o cliente realize autenticação informando usuário e senha.

**RF12.** O sistema deve informar quando a autenticação não puder ser concluída em razão de usuário ou senha inválidos.

**RF13.** O sistema deve permitir que o cliente encerre sua sessão de uso.

**RF14.** O sistema deve permitir que o cliente edite seus dados cadastrais e preferências de perfil.

**RF15.** O sistema deve permitir que o cliente defina idioma de preferência.

**RF16.** O sistema deve permitir que o cliente escolha uma categoria favorita.

**RF17.** O sistema deve permitir que o cliente habilite uma lista personalizada de produtos com base em sua categoria favorita.

**RF18.** O sistema deve permitir que o cliente habilite a exibição de um banner promocional relacionado à sua categoria favorita.

### 4.4. Carrinho de Compras

**RF19.** O sistema deve permitir incluir itens no carrinho de compras a partir das páginas de produto e de detalhe do item.

**RF20.** Quando o mesmo item for adicionado mais de uma vez, o sistema deve consolidar o item no carrinho e aumentar sua quantidade.

**RF21.** O sistema deve permitir visualizar o carrinho com a relação dos itens selecionados, quantidades, preços unitários e totais por item.

**RF22.** O sistema deve informar, para cada item no carrinho, se ele se encontra disponível em estoque no momento da inclusão.

**RF23.** O sistema deve permitir a atualização das quantidades dos itens no carrinho.

**RF24.** O sistema deve permitir a remoção de itens do carrinho.

**RF25.** Quando a quantidade informada para um item for menor que 1, o sistema deve removê-lo do carrinho.

**RF26.** O sistema deve calcular automaticamente o subtotal do carrinho com base nos itens e nas quantidades selecionadas.

### 4.5. Estoque e Disponibilidade

**RF27.** O sistema deve informar a disponibilidade de estoque na visualização do item.

**RF28.** Quando não houver quantidade disponível em estoque, o sistema deve indicar que o item está sob encomenda.

**RF29.** Ao concluir um pedido, o sistema deve registrar a baixa da quantidade comprada no estoque.

### 4.6. Processo de Compra e Pedido

**RF30.** O sistema deve exigir que o usuário esteja autenticado para iniciar o processo de fechamento da compra.

**RF31.** Ao iniciar um pedido, o sistema deve utilizar os dados cadastrais do cliente para preencher inicialmente as informações de cobrança e entrega.

**RF32.** O sistema deve utilizar os itens do carrinho para compor automaticamente o pedido.

**RF33.** O sistema deve permitir ao cliente informar ou ajustar os dados de pagamento do pedido.

**RF34.** O sistema deve permitir a escolha do tipo de cartão dentre as opções disponibilizadas pela aplicação.

**RF35.** O sistema deve permitir que o cliente indique um endereço de entrega diferente do endereço de cobrança.

**RF36.** Quando o cliente optar por endereço de entrega diferente, o sistema deve apresentar uma etapa específica para preenchimento desse endereço.

**RF37.** Antes da finalização, o sistema deve apresentar uma etapa de confirmação com os dados de cobrança e entrega informados.

**RF38.** O sistema deve concluir o pedido somente após a confirmação explícita do cliente.

**RF39.** Ao concluir o pedido, o sistema deve gerar um identificador único para a compra.

**RF40.** Ao concluir o pedido, o sistema deve registrar a data da compra, os itens adquiridos, as quantidades, os valores e a situação inicial do pedido.

**RF41.** Após a conclusão da compra, o sistema deve limpar o carrinho do cliente.

**RF42.** Após a conclusão da compra, o sistema deve exibir mensagem de confirmação de recebimento do pedido.

### 4.7. Consulta de Pedidos

**RF43.** O sistema deve permitir que o cliente consulte a lista de seus pedidos já realizados.

**RF44.** O sistema deve apresentar, na listagem de pedidos, ao menos o número do pedido, a data e o valor total.

**RF45.** O sistema deve permitir a consulta do detalhamento de um pedido específico.

**RF46.** No detalhamento do pedido, o sistema deve apresentar dados de pagamento, endereços, transportadora, status, itens comprados, quantidades, preços e valor total da compra.

**RF47.** O sistema deve restringir a visualização de pedidos ao respectivo cliente responsável pela compra.

## 5. Requisitos Não Funcionais

### 5.1. Segurança e Controle de Acesso

**RNF01.** O sistema deve proteger as funcionalidades de fechamento de compra e consulta de pedidos por meio de autenticação do cliente.

**RNF02.** O sistema deve encerrar adequadamente a sessão do cliente no processo de logout, evitando a continuidade indevida do acesso autenticado.

**RNF03.** O sistema não deve expor desnecessariamente a senha do cliente durante a navegação após o login.

### 5.2. Integridade e Consistência das Informações

**RNF04.** O sistema deve manter consistência entre carrinho, pedido e estoque, evitando divergências entre a compra realizada e os itens registrados.

**RNF05.** O sistema deve garantir que o pedido seja registrado com todos os seus elementos principais, incluindo cabeçalho, status e itens comprados.

**RNF06.** O sistema deve garantir unicidade na numeração dos pedidos, permitindo rastreabilidade das compras.

**RNF07.** O sistema deve calcular automaticamente valores do carrinho e do pedido, reduzindo risco de erro manual.

### 5.3. Confiabilidade Operacional

**RNF08.** O sistema deve tratar entradas inválidas de forma controlada, exibindo mensagens adequadas ao usuário sem comprometer a continuidade da aplicação.

**RNF09.** O sistema deve impedir operações inconsistentes, como iniciar compra sem autenticação ou tentar manipular itens inexistentes de forma silenciosa.

**RNF10.** O sistema deve preservar o histórico de pedidos para consulta posterior pelo cliente.

### 5.4. Usabilidade e Experiência de Uso

**RNF11.** O sistema deve oferecer navegação simples e compreensível, com acesso claro às categorias, busca, carrinho, conta do cliente e ajuda.

**RNF12.** O processo de compra deve ser conduzido em etapas lógicas e progressivas, facilitando o entendimento do cliente durante o checkout.

**RNF13.** O sistema deve fornecer mensagens de orientação e confirmação em pontos importantes do fluxo, como falha de login, campo de busca vazio e pedido concluído.

### 5.5. Atualização das Informações de Negócio

**RNF14.** O sistema deve consultar a situação de estoque de forma atualizada nos pontos críticos da jornada de compra.

**RNF15.** O sistema deve refletir as preferências cadastradas pelo cliente, como lista personalizada e banner associado à categoria favorita.

## 6. Observações

1. Os requisitos aqui descritos foram inferidos com base no comportamento atualmente implementado na aplicação.
2. O documento prioriza a visão de negócio observada no sistema e não substitui uma validação formal com usuários, gestores ou responsáveis pelo produto.
3. Alguns comportamentos identificados no código foram traduzidos para linguagem funcional e organizacional, evitando detalhamento excessivamente técnico.
