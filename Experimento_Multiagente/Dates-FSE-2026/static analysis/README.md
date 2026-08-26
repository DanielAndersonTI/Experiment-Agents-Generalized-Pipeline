# Static Analysis

Esta pasta agora contem um runner de analise estatica baseado em codigo-fonte:

- Script principal: `static analysis/analyze_systems.py`
- Entrada: todos os projetos encontrados em `systems/`
- Saida: `analysis-results/static-analysis/`

## O que o script extrai

- modulos detectados por `pom.xml` e `build.gradle`
- classes e tipos Java por projeto
- pacotes e dependencias entre pacotes baseadas em `import`
- roles inferidos por pacote/anotacao, como `controller`, `service`, `repository`, `domain`
- entrypoints heuristicas, como `main`, `SpringBootApplication` e controladores HTTP

## Como executar

```powershell
python "static analysis\analyze_systems.py"
```

Também é possível executar o mesmo processo pela interface local: abra **Projetos e
análise estática**, expanda **Atualizar a análise estática dos oito projetos**, confirme
a ação e clique em **Executar análise estática**. Essa operação não chama um LLM e
sobrescreve os artefatos em `analysis-results/static-analysis/`.

## Artefatos gerados por projeto

- `summary.json`
- `modules.csv`
- `classes.csv`
- `package_dependencies.csv`
- `package_metrics.csv`
- `entrypoints.csv`

O campo de arquivos de build representa `pom.xml` e `build.gradle` detectados. Ele é
uma indicação de módulos de build, não uma contagem garantida de módulos de negócio.

## Artefatos consolidados

- `analysis-results/static-analysis/index.json`
- `analysis-results/static-analysis/project_summaries.csv`
- `analysis-results/static-analysis/manifest.json`

## Observacao

O ambiente atual nao possui `java` nem `maven` no `PATH`. Por isso a metodologia adotada aqui faz analise estatica offline pelo codigo-fonte e pela estrutura de build, sem depender de compilacao local dos 8 sistemas.

As dependências internas são inferidas de declarações `import`; portanto, descrevem
relações estáticas de código e não chamadas, tráfego ou comportamento de runtime.
