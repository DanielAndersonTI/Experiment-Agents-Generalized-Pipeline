# Microservice Decomposition Pipeline

Este repositório agora contém um pipeline em Python para gerar propostas de decomposição de sistemas monolíticos em microsserviços usando LLMs via API.

Para instalar o projeto em outra máquina e executar o fluxo completo, siga o guia
[Instalação e execução local](docs/LOCAL_SETUP.md). Ele inclui ambiente virtual,
configuração de chaves, modo seco, DeepSeek, comparação e interface gráfica.

O pipeline combina:

- requisitos funcionais em CSV localizados dentro de `systems/`
- resultados de análise estática localizados em `analysis-results/static-analysis/`

Para cada combinação de projeto, provedor/modelo e template de prompt, o pipeline solicita uma proposta de arquitetura e salva uma única saída final em CSV.

## Estrutura principal

```text
.
├── systems/
├── analysis-results/static-analysis/
├── outputs/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── project_loader.py
│   ├── static_analysis_loader.py
│   ├── requirements_loader.py
│   ├── prompt_builder.py
│   ├── agentic/
│   │   ├── workflow.py
│   │   └── trace.py
│   ├── llm_clients/
│   │   ├── openai_client.py
│   │   ├── anthropic_client.py
│   │   └── deepseek_client.py
│   ├── response_parser.py
│   ├── csv_writer.py
│   └── metadata_writer.py
├── config.yaml
├── requirements.txt
└── .env.example
```

## Configuração

1. Crie e ative um ambiente virtual Python.
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Crie um arquivo `.env` a partir de `.env.example`:

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
DEEPSEEK_API_KEY=...
```

O `.env.example` contém os nomes das variáveis sem segredos e o `.env` é ignorado pelo
Git. Preencha somente as chaves dos provedores que você realmente utilizará.

4. Ajuste os modelos em `config.yaml` se quiser trocar os defaults.

Os nomes de modelo, número de runs, tentativas máximas e templates ficam configuráveis em `config.yaml` e também podem ser filtrados pela CLI. O padrão atual é `1` execução por combinação.

Se algum modelo novo reclamar de parâmetros como `temperature`, você pode definir:

```yaml
temperature: null
```

O pipeline também tenta fazer retry automático sem `temperature` quando a API indicar que o parâmetro foi descontinuado para aquele modelo.
Para modelos `gpt-5*`, o client já evita enviar `temperature` por padrão.

## Como executar

Executar todos os experimentos:

```bash
python -m src.main --systems-dir systems --static-analysis-dir analysis-results/static-analysis --output-dir outputs
```

Executar para todos os provedores habilitados no `config.yaml` e salvar os prompts:

```bash
python -m src.main --output-dir outputs --save-prompts
```

Executar apenas um projeto:

```bash
python -m src.main --project 7ep
```

Executar apenas um provedor/modelo/template:

```bash
python -m src.main --project pet-clinic --provider openai --model gpt-5.5-2026-04-23 --prompt-template zero_shot
```

Validar descoberta e construção dos prompts sem chamar API:

```bash
python -m src.main --project 7ep --provider openai --prompt-template zero_shot --runs 1 --dry-run
```

Ver os prompts no terminal sem chamar API:

```bash
python -m src.main --project 7ep --dry-run --print-prompts
```

Salvar os prompts em arquivo:

```bash
python -m src.main --project 7ep --provider openai --save-prompts
```

## Templates de prompt

Atualmente o pipeline implementa:

- `zero_shot`
- `few_shot`

O template `few_shot` adiciona três exemplos genéricos antes dos dados reais para orientar o modelo sem contaminar o domínio do sistema analisado.

## Estratégia de saída

Cada chamada ao modelo pede JSON estruturado neste formato:

```json
{
  "microservices": [
    {
      "microservice_name": "Order Service",
      "responsibility": "Manages order creation, order status, and order history.",
      "communicates_with": ["Customer Service", "Payment Service"]
    }
  ]
}
```

O pipeline:

1. valida o JSON com Pydantic
2. tenta reparar respostas quase válidas
3. repete a chamada até o limite configurado se necessário
4. converte a resposta validada para CSV

O CSV final sempre tem exatamente 3 colunas:

```csv
microservice_name,responsibility,communicates_with
Order Service,"Manages order creation, order status, and order history.","Customer Service;Payment Service"
```

## Onde os resultados ficam

Os arquivos de saída ficam organizados em:

```text
outputs/{project_name}/{approach}/{provider}/{model_name}/{prompt_template}/run_{n}.csv
```

Se `--save-prompts` for usado, o pipeline também salva:

```text
outputs/{project_name}/{approach}/{provider}/{model_name}/{prompt_template}/run_{n}.prompt.txt
```

Cada execução também gera `run_{n}.trace.jsonl`, com as chamadas e o resultado de cada etapa.

Também é criado:

```text
outputs/metadata.csv
```

Esse arquivo registra:

- projeto
- abordagem
- provedor
- modelo
- template
- run
- caminho do arquivo
- caminho do trace
- timestamp
- status
- erro, se houver

## Observações

- As chaves de API não ficam hardcoded no código.
- O loader de requisitos é tolerante a nomes de colunas diferentes.
- O loader de análise estática aceita `.csv`, `.json`, `.txt` e `.md`.
- O pipeline usa por padrão a análise estática já gerada em `analysis-results/static-analysis/`.

## Abordagens de geração

O pipeline oferece duas formas de gerar a proposta:

- `direct` (padrão): uma chamada ao modelo com todos os requisitos e evidências estruturais.
- `agent`: um fluxo estruturado com analistas de domínio e estrutura, um arquiteto, um crítico e um refinador. O crítico pode solicitar revisões até o limite `experiment.agent.max_refinement_rounds`.

Para executar as duas abordagens para o mesmo caso:

```bash
python -m src.main --project pet-clinic --approach direct --approach agent --runs 3 --save-prompts
```

Use `--dry-run` para conferir a descoberta dos arquivos e a construção dos prompts sem chamar um provedor de LLM.

### Fluxo por agente

Na abordagem `agent`, os papéis são chamadas especializadas ao modelo, coordenadas por
`src/agentic/workflow.py`:

```text
analista de domínio + analista estrutural
                ↓
            arquiteto
                ↓
             crítico ── aprovado ──> proposta final
                │
                └── revisão necessária ──> refinador ──> crítico
```

O crítico recebe a proposta candidata, as duas análises e as evidências originais. Ele
retorna `requires_revision` e uma lista estruturada de problemas. O refinador só é
chamado quando `requires_revision=true`; ele recebe a crítica e deve preservar as
decisões válidas. O ciclo termina quando o crítico aprova ou quando atinge
`experiment.agent.max_refinement_rounds`. Com `R` rodadas máximas, o fluxo faz de 4
a `3 + 2R` chamadas lógicas ao LLM, antes das tentativas de repetição por erro.

## Comparação entre abordagens

O módulo `src/comparison/` calcula métricas automáticas a partir dos CSVs finais e dos traces das execuções `direct` e `agent`.

```bash
python -m src.comparison.evaluate --outputs-dir outputs --comparison-dir comparison_outputs
```

Consulte [src/comparison/README.md](src/comparison/README.md) para as fórmulas, os relatórios gerados, o pareamento das execuções e as limitações das métricas.

## Interface gráfica local

A interface Streamlit reúne a exploração dos projetos, a análise estática, as prévias de prompt, o fluxo por agente, a execução de experimentos, os resultados e a comparação entre estratégias.

```bash
python -m pip install -r requirements.txt
python -m streamlit run src/ui/app.py --server.address localhost
```

Por padrão, a configuração do repositório limita o servidor ao `localhost`. Consulte [src/ui/README.md](src/ui/README.md) para o roteiro de uso, os cuidados com chaves de API e os artefatos exibidos.

## Fluxo recomendado com DeepSeek

1. Configure `DEEPSEEK_API_KEY` no `.env` e mantenha `deepseek` habilitado em
   `config.yaml`.
2. Atualize a análise estática em **Projetos e análise estática** ou execute o runner
   descrito em [static analysis/README.md](static%20analysis/README.md).
3. Em **Executar experimentos**, escolha `deepseek` / `deepseek-chat`, as abordagens
   `direct` e `agent`, os templates desejados e execute primeiro em **Modo seco**.
4. Após conferir as prévias, execute a condição real. Ela pode gerar custo de API e
   reexecutar uma condição substitui CSV, trace e prompt daquele caminho; o
   `metadata.csv` mantém o histórico.
5. Abra **Resultados gerados** para inspecionar o CSV, prompt e trace. Por fim, use
   **Comparação** para calcular relatórios sem chamar o LLM novamente.
