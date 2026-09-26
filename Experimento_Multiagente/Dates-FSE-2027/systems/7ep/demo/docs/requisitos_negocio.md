# Requisitos da Aplicacao

Este documento resume requisitos inferidos do codigo atual da aplicacao, com foco nas regras de negocio e no comportamento esperado pelo usuario. Sempre que houver diferenca entre o que existe na camada de regra de negocio e o que aparece na tela principal, isso sera observado ao final.

## Requisitos funcionais

### 1. Acesso de bibliotecarios

- RF01. O sistema deve permitir o cadastro de bibliotecarios por meio de nome de usuario e senha.
- RF02. O sistema nao deve permitir o cadastro de um bibliotecario com nome de usuario ja existente.
- RF03. O sistema deve exigir o preenchimento de nome de usuario e senha no cadastro.
- RF04. O sistema deve aceitar apenas senhas consideradas fortes o suficiente para uso seguro.
- RF05. O sistema deve rejeitar senhas muito curtas.
- RF06. O sistema deve permitir que bibliotecarios autenticados informem nome de usuario e senha para entrar no sistema.
- RF07. O sistema deve conceder acesso somente quando usuario e senha corresponderem exatamente ao cadastro existente.
- RF08. O sistema deve negar o acesso quando usuario ou senha estiverem incorretos ou nao forem informados.

### 2. Cadastro e manutencao de livros

- RF09. O sistema deve permitir o cadastro de livros no acervo por titulo.
- RF10. O sistema nao deve permitir o cadastro duplicado de um mesmo livro.
- RF11. O sistema deve informar quando a tentativa de cadastro de livro falhar por falta de titulo.
- RF12. O sistema deve permitir a exclusao de livros ja cadastrados.
- RF13. O sistema nao deve permitir a exclusao de livros que nunca foram cadastrados.
- RF14. O sistema deve excluir tambem o vinculo de emprestimo quando um livro removido estiver emprestado.

### 3. Cadastro e manutencao de leitores

- RF15. O sistema deve permitir o cadastro de leitores aptos a receber emprestimos.
- RF16. O sistema nao deve permitir o cadastro duplicado de um mesmo leitor.
- RF17. O sistema deve informar quando a tentativa de cadastro de leitor falhar por falta de nome.
- RF18. O sistema deve permitir a exclusao de leitores ja cadastrados.
- RF19. O sistema nao deve permitir a exclusao de leitores que nunca foram cadastrados.
- RF20. O sistema deve excluir tambem os vinculos de emprestimo quando um leitor removido possuir livros emprestados.

### 4. Emprestimo de livros

- RF21. O sistema deve permitir registrar o emprestimo de um livro para um leitor cadastrado.
- RF22. O sistema deve registrar a data em que o emprestimo foi realizado.
- RF23. O sistema nao deve permitir emprestimo para pessoa que nao esteja cadastrada como leitora.
- RF24. O sistema nao deve permitir emprestimo de livro que nao esteja cadastrado.
- RF25. O sistema nao deve permitir emprestimo de livro que ja esteja emprestado a outra pessoa.
- RF26. O sistema deve permitir que um mesmo leitor tenha mais de um livro emprestado ao mesmo tempo.
- RF27. O sistema deve garantir que um mesmo livro esteja emprestado para apenas um leitor por vez.
- RF28. O sistema deve informar claramente quando um emprestimo nao puder ser concluido.

### 5. Consulta de acervo e leitores

- RF29. O sistema deve permitir listar todos os livros cadastrados.
- RF30. O sistema deve permitir consultar um livro por identificador.
- RF31. O sistema deve permitir consultar um livro por titulo.
- RF32. O sistema deve informar quando nao houver livros cadastrados ou quando uma busca nao encontrar resultado.
- RF33. O sistema deve permitir listar apenas os livros disponiveis para emprestimo.
- RF34. O sistema deve permitir listar todos os leitores cadastrados.
- RF35. O sistema deve permitir consultar um leitor por identificador.
- RF36. O sistema deve permitir consultar um leitor por nome.
- RF37. O sistema deve informar quando nao houver leitores cadastrados ou quando uma busca nao encontrar resultado.
- RF38. O sistema nao deve aceitar, na mesma consulta, busca simultanea por identificador e por nome/titulo.

### 6. Apoio operacional da interface

- RF39. O sistema deve facilitar o preenchimento do emprestimo exibindo opcoes de livros disponiveis e leitores cadastrados.
- RF40. O sistema deve adaptar a forma de escolha na tela de emprestimo conforme a quantidade de opcoes disponiveis, usando selecao direta quando houver poucas opcoes e sugestoes de busca quando houver muitas.
- RF41. O sistema deve bloquear o campo de selecao de emprestimo quando nao houver dados disponiveis para escolha.
- RF42. O sistema deve exibir o resultado de cada operacao de forma imediata apos o envio do formulario.

### 7. Administracao do ambiente de demonstracao

- RF43. O sistema deve permitir limpar os dados e a estrutura da base para reiniciar o ambiente.
- RF44. O sistema deve permitir recriar a estrutura da base quando necessario.
- RF45. O sistema deve permitir restaurar rapidamente o ambiente para um estado limpo e pronto para novos testes.

### 8. Funcionalidades auxiliares e demonstrativas

- RF46. O sistema deve oferecer um catalogo de servicos para consulta e teste de endpoints disponiveis.
- RF47. O sistema deve permitir somar dois numeros inteiros informados pelo usuario.
- RF48. O sistema deve permitir calcular valores da sequencia de Fibonacci com mais de uma abordagem de calculo.
- RF49. O sistema deve permitir calcular resultados da funcao de Ackermann com mais de uma abordagem de calculo.
- RF50. O sistema deve informar erro quando os servicos matematicos receberem valores fora do formato esperado.

## Requisitos nao funcionais

### 1. Seguranca e protecao de acesso

- RNF01. O sistema deve tratar credenciais de bibliotecarios de forma protegida, sem depender da senha em texto puro para validacao posterior.
- RNF02. O sistema deve exigir senhas com nivel minimo de robustez antes de concluir o cadastro de um bibliotecario.
- RNF03. O sistema deve responder de forma clara a tentativas de acesso negadas, sem expor detalhes sensiveis do processamento interno.

### 2. Integridade das informacoes

- RNF04. O sistema deve preservar a consistencia entre livros, leitores e emprestimos, evitando registros invalidos ou contraditorios.
- RNF05. O sistema deve impedir duplicidades nos cadastros principais quando o registro ja existir.
- RNF06. O sistema deve manter a base coerente quando livros ou leitores forem excluidos, removendo tambem os emprestimos vinculados.
- RNF07. O sistema deve validar dados obrigatorios antes de executar operacoes de negocio.

### 3. Usabilidade

- RNF08. O sistema deve poder ser utilizado por meio de formularios web simples, com retorno rapido e legivel para cada acao.
- RNF09. O sistema deve oferecer mensagens objetivas de sucesso, negacao e erro para orientar o usuario.
- RNF10. O sistema deve reduzir digitacao manual em fluxos repetitivos, como emprestimo de livros, por meio de listas ou sugestoes.
- RNF11. O sistema deve funcionar em navegadores comuns e considerar uso em telas menores.

### 4. Confiabilidade operacional

- RNF12. O sistema deve permitir reiniciar o ambiente de dados de forma previsivel para repeticao de testes e demonstracoes.
- RNF13. O sistema deve manter comportamento consistente tanto pela interface principal quanto pelos endpoints de consulta e envio de dados.
- RNF14. O sistema deve registrar as principais operacoes para apoiar rastreabilidade e analise de problemas.

### 5. Qualidade e evolucao

- RNF15. As regras centrais de cadastro, autenticacao, consulta e emprestimo devem ser verificadas de forma repetivel por testes automatizados.
- RNF16. O sistema deve estar organizado por dominios de negocio, favorecendo manutencao e ampliacao das funcionalidades.

## Observacoes do levantamento

- O codigo implementa regras de exclusao de livros e leitores, mas a tela principal atual nao expoe esses comandos diretamente.
- O sistema possui autenticacao de bibliotecarios, mas o codigo atual nao mostra bloqueio de sessao nas demais operacoes da biblioteca.
- A parte de biblioteca e autenticacao e o nucleo de negocio mais claro da aplicacao; os modulos matematicos aparecem como funcionalidades auxiliares de demonstracao.
