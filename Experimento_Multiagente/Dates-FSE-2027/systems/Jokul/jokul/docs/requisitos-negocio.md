# Requisitos de Negocio da Aplicacao

Este documento foi levantado com base no comportamento observado no codigo do projeto `jokul-client` e `jokul-server`.

O foco aqui esta nas regras de negocio e nas expectativas funcionais da aplicacao, evitando detalhamento excessivamente tecnico.

## 1. Requisitos funcionais

### 1.1. Acesso e perfis

- RF01. O sistema deve permitir cadastro de usuarios com nome de usuario e senha.
- RF02. O sistema deve permitir login de usuarios ja cadastrados.
- RF03. O sistema deve diferenciar pelo menos dois perfis de uso: usuario comum e administrador.
- RF04. O sistema deve negar o acesso quando o usuario nao existir, quando a senha estiver incorreta ou quando o perfil informado nao corresponder ao cadastro.
- RF05. O sistema deve manter a identificacao do usuario logado durante a navegacao no navegador.
- RF06. O sistema deve exibir a area de gestao de recursos apenas para usuarios identificados como administradores.
- RF07. O sistema deve permitir que o usuario encerre a sessao.

### 1.2. Catalogo de filmes

- RF08. O sistema deve exibir uma pagina inicial com a listagem de filmes disponiveis.
- RF09. Cada filme listado deve apresentar, no minimo, titulo, poster e nota.
- RF10. O sistema deve organizar a listagem de filmes em paginas.
- RF11. O sistema deve permitir a consulta da quantidade total de filmes cadastrados para suportar a navegacao paginada.
- RF12. O sistema deve permitir abrir a pagina de detalhes de um filme a partir da listagem.

### 1.3. Consulta de detalhes do filme

- RF13. O sistema deve apresentar uma pagina de detalhes para cada filme.
- RF14. A pagina de detalhes deve exibir, no minimo, titulo, nota, nome alternativo, data de lancamento, duracao, direcao, roteiro, elenco, sinopse, poster e categorias.
- RF15. O sistema deve permitir visualizar o elenco completo do filme.
- RF16. O sistema deve impedir a consulta de detalhes de filmes inexistentes, retornando uma mensagem de erro apropriada.

### 1.4. Categorias e descoberta de conteudo

- RF17. O sistema deve disponibilizar uma area de navegacao por categorias de filmes.
- RF18. O sistema deve permitir visualizar todas as categorias cadastradas.
- RF19. O sistema deve permitir listar apenas os filmes pertencentes a uma categoria selecionada.
- RF20. Um filme deve poder pertencer a mais de uma categoria.
- RF21. O sistema deve permitir voltar da visao por categoria para a visao geral do catalogo.

### 1.5. Reproducao e acesso ao arquivo do filme

- RF22. O sistema deve permitir iniciar a reproducao de um filme a partir da sua pagina de detalhes.
- RF23. O sistema deve disponibilizar um link para download do arquivo do filme quando o recurso estiver pronto para consumo.
- RF24. Antes da reproducao, o sistema deve garantir que o arquivo de video esteja disponivel na area usada pela aplicacao para entrega do conteudo.
- RF25. Se o arquivo ainda nao estiver disponivel nessa area de entrega, o sistema deve tentar obtelo a partir do repositorio local configurado.

### 1.6. Administracao do acervo

- RF26. O administrador deve poder cadastrar um novo filme no catalogo.
- RF27. O cadastro de filme deve incluir, no minimo, titulo, nota, nome alternativo, data de lancamento, duracao, direcao, roteiro, elenco, categorias, sinopse e poster.
- RF28. O sistema deve impedir o cadastro duplicado de filmes com o mesmo titulo.
- RF29. O administrador deve poder enviar o arquivo de video do filme para a aplicacao.
- RF30. O administrador deve poder excluir um filme do catalogo.
- RF31. O sistema deve permitir a exclusao em lote de mais de um filme.
- RF32. O sistema deve informar ao administrador quais filmes foram selecionados antes da exclusao em lote.
- RF33. O sistema deve impedir a exclusao de filmes inexistentes.

### 1.7. Regras de consistencia do cadastro

- RF34. O sistema deve impedir cadastro duplicado de usuarios com o mesmo nome de usuario.
- RF35. O titulo do filme deve ser tratado como identificador unico do cadastro no catalogo.
- RF36. O processo padrao de reproducao pressupoe que o arquivo fisico do filme tenha correspondencia com o titulo cadastrado.

## 2. Requisitos nao funcionais

### 2.1. Experiencia de uso

- RNF01. A aplicacao deve ser acessivel por interface web.
- RNF02. A navegacao do catalogo deve ser simples e direta, com acesso visivel a pagina inicial, categorias, detalhes e reproducao.
- RNF03. A aplicacao deve apresentar mensagens claras de sucesso, alerta e falha nas operacoes principais, como login, cadastro, inclusao, exclusao, upload e reproducao.
- RNF04. A exibicao do catalogo deve ser paginada em blocos de ate 12 filmes por pagina, favorecendo organizacao visual e desempenho percebido.

### 2.2. Integridade e confiabilidade

- RNF05. O sistema deve manter um padrao unico de resposta para as operacoes, indicando status, mensagem e dados retornados.
- RNF06. As informacoes de usuarios, filmes e categorias devem ser persistidas de forma duravel.
- RNF07. O sistema deve preservar a unicidade de usuarios e filmes para evitar duplicidades no acervo e no acesso.
- RNF08. O tratamento de erros deve retornar mensagens controladas ao usuario sempre que possivel.

### 2.3. Seguranca e controle de acesso

- RNF09. O sistema deve operar com separacao de perfis entre usuario comum e administrador.
- RNF10. Funcoes de gestao do acervo devem ser restritas ao perfil administrador.
- RNF11. A sessao do usuario deve permanecer identificada no navegador ate que ele realize logout ou limpe seus dados locais.

### 2.4. Midia e armazenamento

- RNF12. O sistema deve suportar upload de arquivos de video grandes, de ate 2 GB por arquivo.
- RNF13. O processo operacional da aplicacao deve considerar o formato MP4 como formato padrao de video.
- RNF14. O ambiente da aplicacao deve possuir uma area local para armazenar temporariamente ou servir os arquivos de video consumidos na reproducao.
- RNF15. O ambiente da aplicacao deve possuir um repositorio local configurado de onde os filmes possam ser carregados sob demanda.

### 2.5. Integracao e arquitetura operacional

- RNF16. A solucao deve permitir que a interface do usuario e os servicos da aplicacao evoluam de forma separada.
- RNF17. A interface do usuario deve conseguir consumir os servicos da aplicacao mesmo quando estiver publicada em ambiente distinto.
- RNF18. Os dados de usuarios, filmes e categorias devem ser armazenados em uma base estruturada que suporte os relacionamentos do catalogo.

## 3. Regras e restricoes de negocio observadas

- RN01. O sistema trabalha com dois tipos de usuario: comum e administrador.
- RN02. Um filme pode ter varias categorias associadas.
- RN03. O envio do arquivo de video e o cadastro do filme sao etapas relacionadas, mas independentes.
- RN04. A reproducao automatica depende da existencia de um arquivo MP4 correspondente ao titulo cadastrado.
- RN05. O nome do arquivo de origem do filme precisa seguir o padrao esperado pela configuracao do ambiente para que a carga automatica funcione.

## 4. Observacoes sobre o estado atual do codigo

- OBS01. A intencao de restringir a gestao de recursos ao administrador esta clara na interface, mas essa restricao nao aparece validada de forma completa no backend.
- OBS02. O sistema atual esta mais orientado a um acervo local de filmes do que a um armazenamento remoto ou servico de streaming externo.
- OBS03. A disponibilidade para reproducao depende tanto do cadastro do filme quanto da existencia do arquivo fisico correspondente.
