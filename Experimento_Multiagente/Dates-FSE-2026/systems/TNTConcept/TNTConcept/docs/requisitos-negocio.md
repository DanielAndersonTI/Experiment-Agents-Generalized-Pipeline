# Requisitos da Aplicação

Levantamento elaborado a partir do código da aplicação `TNTConcept`, com foco em regras de negócio e comportamento funcional já existente.

## Requisitos Funcionais

### 1. Administração e cadastros de apoio

- `RF-ADM-01` O sistema deve permitir manter cadastros de apoio usados pelas demais áreas, como departamentos, tipos de contrato, categorias de usuário, tipos de organização, tipos de interação, motivos tributários, regimes de faturamento e frequências.
- `RF-ADM-02` O sistema deve permitir cadastrar e manter projetos vinculados a clientes, com período de vigência, situação aberta ou encerrada, papéis envolvidos e custos relacionados.
- `RF-ADM-03` O sistema deve permitir manter acordos de trabalho com regras vigentes por período, incluindo carga anual de trabalho e quantidade de férias.
- `RF-ADM-04` O sistema deve permitir configurações individuais por usuário para personalizar o uso da aplicação.

### 2. Pessoas, acessos e RH

- `RF-RH-01` O sistema deve permitir cadastrar e manter usuários com dados pessoais, contratuais, departamento, categoria, perfil de acesso e acordo de trabalho.
- `RF-RH-02` O sistema deve permitir alterar senha, resetar senha administrativamente e obrigar a renovação da senha quando ela expirar.
- `RF-RH-03` O sistema deve impedir a troca de senha quando a senha atual estiver incorreta, quando a nova senha não for confirmada corretamente ou quando a nova senha for igual à anterior.
- `RF-RH-04` O sistema deve permitir registrar solicitações de férias com datas de início e fim, ano de compensação, comentários do solicitante e observações da análise.
- `RF-RH-05` O sistema deve controlar o ciclo da solicitação de férias com os estados pendente, aceita, rejeitada e cancelada.
- `RF-RH-06` O sistema deve impedir solicitações de férias com intervalo de datas inválido.
- `RF-RH-07` O sistema deve impedir solicitações que ultrapassem o saldo disponível de férias do colaborador.
- `RF-RH-08` O sistema deve calcular o saldo de férias considerando somente dias úteis, desconsiderando fins de semana e feriados.
- `RF-RH-09` O sistema deve calcular o direito anual de férias de forma proporcional quando o colaborador estiver no primeiro ano de contrato.
- `RF-RH-10` O sistema deve considerar somente solicitações aprovadas para abatimento do saldo de férias.
- `RF-RH-11` O sistema deve notificar por e-mail os aprovadores configurados quando uma nova solicitação de férias for registrada.
- `RF-RH-12` O sistema deve avisar por e-mail quando contratos ou períodos de experiência estiverem próximos do vencimento.

### 3. Relacionamento comercial e CRM

- `RF-CRM-01` O sistema deve permitir cadastrar e manter organizações, contatos, colaboradores externos, cargos e tipos de interação.
- `RF-CRM-02` O sistema deve permitir registrar interações comerciais e de relacionamento vinculadas a contatos, propostas e projetos.
- `RF-CRM-03` O sistema deve permitir pesquisar contatos por critérios avançados e exportar o resultado para CSV.
- `RF-CRM-04` O sistema deve permitir classificar propostas por potencial de negócio, em níveis como alto, médio e baixo.
- `RF-CRM-05` O sistema deve controlar o ciclo da proposta com os estados aberta, aceita e rejeitada.
- `RF-CRM-06` O sistema deve permitir registrar motivos de rejeição de propostas.
- `RF-CRM-07` O sistema deve permitir compor propostas com papéis de trabalho, horas previstas, materiais, custos e indicação do que pode ou não ser faturado.
- `RF-CRM-08` O sistema deve permitir duplicar uma proposta preservando sua composição, mas sem reaproveitar identificadores únicos.
- `RF-CRM-09` O sistema deve permitir converter uma proposta em rascunho de faturamento, reaproveitando contato, descrição e itens faturáveis.

### 4. Projetos, atividades e operação

- `RF-OPE-01` O sistema deve permitir registrar atividades internas e externas por colaborador, data, cliente, projeto, papel executado e descrição.
- `RF-OPE-02` O sistema deve priorizar, no apontamento operacional, projetos abertos e papéis válidos para execução.
- `RF-OPE-03` O sistema deve permitir classificar atividades como faturáveis ou não faturáveis.
- `RF-OPE-04` O sistema deve diferenciar o tempo que compõe jornada de trabalho do tempo que não compõe jornada, para cálculo correto de horas trabalhadas.
- `RF-OPE-05` O sistema deve permitir manter objetivos e ocupações vinculados à rotina operacional.
- `RF-OPE-06` O sistema deve apresentar relatórios consolidados de horas por usuário, projeto e organização.
- `RF-OPE-07` O sistema deve permitir anexar evidências às atividades quando o projeto ou papel exigir comprovação.
- `RF-OPE-08` O sistema deve suportar políticas de evidência como sem exigência, exigência única ou exigência semanal.
- `RF-OPE-09` O sistema deve alertar por e-mail os colaboradores que tenham atividades recentes em projetos com exigência semanal de evidência, mas ainda sem comprovação anexada.

### 5. Financeiro e faturamento

- `RF-FIN-01` O sistema deve permitir manter contas, tipos de lançamento, grupos de lançamento e lançamentos financeiros periódicos.
- `RF-FIN-02` O sistema deve permitir copiar lançamentos periódicos para reaproveitar recorrências financeiras.
- `RF-FIN-03` O sistema deve permitir registrar contas a receber e contas a pagar por meio de faturamentos emitidos e recebidos.
- `RF-FIN-04` O sistema deve permitir detalhar faturamentos por itens, quantidades, valores, tributos, observações e anexos.
- `RF-FIN-05` O sistema deve calcular automaticamente o valor total do faturamento a partir dos itens detalhados.
- `RF-FIN-06` O sistema deve calcular automaticamente o valor líquido a pagar quando houver retenção de IRPF para fornecedores autônomos.
- `RF-FIN-07` O sistema deve permitir registrar múltiplos vencimentos para um mesmo faturamento.
- `RF-FIN-08` O vencimento principal do faturamento deve refletir a data do último pagamento previsto.
- `RF-FIN-09` O sistema deve permitir importar para o faturamento horas faturáveis e custos de projeto já registrados na operação.
- `RF-FIN-10` O sistema deve permitir converter itens faturáveis de propostas em itens de faturamento.
- `RF-FIN-11` O sistema deve calcular automaticamente o saldo em aberto do faturamento com base nos lançamentos financeiros associados.
- `RF-FIN-12` O sistema deve marcar o faturamento como pago quando os lançamentos financeiros cobrirem o valor total devido.
- `RF-FIN-13` O sistema deve permitir associar faturamentos a títulos de crédito, alterando o estado do faturamento para refletir essa vinculação.
- `RF-FIN-14` O sistema deve permitir que a associação a um título de crédito gere ou não um novo vencimento, conforme a escolha do usuário.
- `RF-FIN-15` O sistema deve permitir acompanhar indicadores financeiros, títulos de crédito, necessidade operacional de fundos e rotinas fiscais já contempladas no sistema.

### 6. Documentos, conteúdo e comunicação interna

- `RF-DOC-01` O sistema deve permitir organizar documentos por categorias.
- `RF-DOC-02` O sistema deve permitir manter versões de um mesmo documento, com arquivo, data e identificação da versão.
- `RF-DOC-03` O sistema deve permitir associar documentos a responsáveis e áreas organizacionais.
- `RF-DOC-04` O sistema deve criar e manter automaticamente uma categoria documental própria para cada usuário, permitindo separar documentação individual.
- `RF-DOC-05` O sistema deve permitir navegar dos dados do usuário para sua documentação associada.
- `RF-DOC-06` O sistema deve permitir manter publicações, revistas e tutoriais como base de conhecimento institucional.
- `RF-DOC-07` O sistema deve permitir manter murais de avisos por categoria.
- `RF-DOC-08` O sistema deve exibir avisos públicos na entrada do sistema.
- `RF-DOC-09` O sistema deve permitir manter outros conteúdos de apoio à gestão, como ideias, inventário, tags e links.

### 7. Pedidos e comissionamentos

- `RF-COM-01` O sistema deve permitir registrar pedidos/comissionamentos vinculados a projetos, revisores, colaboradores e dados de pagamento.
- `RF-COM-02` O sistema deve controlar o fluxo do pedido com estados como criado, aprovado, aceito, confirmado, validado e finalizado.
- `RF-COM-03` O sistema deve permitir registrar atrasos, alterações e arquivos relacionados ao pedido.
- `RF-COM-04` O sistema deve preservar o histórico textual das mudanças ocorridas ao longo do fluxo do pedido.
- `RF-COM-05` O sistema deve permitir o envio por e-mail de documentos relacionados ao pedido.

### 8. Relatórios e saídas de informação

- `RF-REL-01` O sistema deve disponibilizar relatórios por domínio de negócio, incluindo faturamento, horas, projetos, propostas, interações, organizações, uso pessoal e comissionamentos.
- `RF-REL-02` O sistema deve permitir exportar relatórios em múltiplos formatos, incluindo CSV, PDF, HTML, RTF, XLS e ODT.
- `RF-REL-03` O sistema deve permitir exportar consultas operacionais específicas, como busca avançada de contatos e relatório global de horas, em formato CSV.

## Requisitos Não Funcionais

### 1. Segurança e controle de acesso

- `RNF-SEG-01` O sistema deve controlar acesso por perfil de usuário, com níveis distintos como administrador, supervisor, equipe interna, usuário comum, gerente de projeto e cliente.
- `RNF-SEG-02` O sistema deve restringir operações sensíveis por escopo de atuação, permitindo regras como acesso total, acesso somente aos próprios registros ou acesso por área.
- `RNF-SEG-03` O sistema deve suportar autenticação local e autenticação via LDAP, conforme configuração do ambiente.
- `RNF-SEG-04` O sistema deve aplicar controle de acesso também sobre documentos, faturamentos, usuários e demais entidades críticas.

### 2. Confiabilidade das regras de negócio

- `RNF-CON-01` O sistema deve realizar automaticamente cálculos críticos de negócio, como saldo de férias, total do faturamento, saldo em aberto, retenções e vencimento final.
- `RNF-CON-02` O sistema deve manter coerência entre módulos relacionados, como usuário e sua pasta documental, proposta e faturamento, faturamento e título de crédito.
- `RNF-CON-03` O sistema deve preservar versões documentais e histórico de alterações em processos que exigem rastreabilidade, como documentos e comissionamentos.

### 3. Comunicação e integração operacional

- `RNF-COM-01` O sistema deve permitir envio de notificações por e-mail para eventos relevantes de negócio, como férias, expiração contratual, redefinição de senha, evidências pendentes e pedidos.
- `RNF-COM-02` O sistema deve gerar saídas interoperáveis para consumo externo, especialmente por meio de arquivos CSV e relatórios em formatos de mercado.

### 4. Operação e continuidade

- `RNF-OPE-01` O sistema deve operar com armazenamento externo para anexos e relatórios, de forma a manter documentos e saídas organizados fora da aplicação.
- `RNF-OPE-02` O sistema deve validar, na inicialização, se os diretórios e arquivos essenciais de configuração estão disponíveis.
- `RNF-OPE-03` O sistema deve preparar automaticamente a estrutura mínima necessária para armazenamento de arquivos enviados pelos usuários.
- `RNF-OPE-04` O sistema deve permitir que regras operacionais específicas sejam habilitadas ou desabilitadas por configuração, como edição de faturamentos, uso de LDAP e envio de notificações.

### 5. Usabilidade e padronização de uso

- `RNF-USA-01` O sistema deve oferecer navegação padronizada baseada em consulta, detalhe, edição, criação e pesquisa para os principais módulos.
- `RNF-USA-02` O sistema deve apoiar a rotina do usuário com filtros, ordenação, pesquisas por período, atalhos de navegação e valores padrão coerentes com o contexto de uso.
- `RNF-USA-03` O sistema deve permitir exportação e visualização de informações de forma simples para apoiar decisões operacionais e gerenciais.

### 6. Idioma e interoperabilidade textual

- `RNF-IDI-01` O sistema deve suportar, no mínimo, português, espanhol e inglês nas mensagens e textos de interface.
- `RNF-IDI-02` O sistema deve tratar textos e arquivos com codificação compatível com caracteres internacionais, preservando nomes, descrições e conteúdos multilíngues.
