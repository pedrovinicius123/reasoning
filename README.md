# Reasoning

API Flask para gerar grafos de conhecimento matemático com modelos Ollama e verificar conexões Lean via AXLE. A aplicação também inclui uma interface web para acompanhar execuções, explorar grafos persistidos e ler a síntese do Writer.

## Como funciona

O agente Creative propõe proposições e conexões em formato JSON. Cada conexão contém uma declaração Lean e uma tentativa de prova; o AXLE verifica a tentativa antes de ela entrar no grafo. Lotes aprovados são persistidos e enviados ao cliente conforme a execução avança. O agente Writer transforma somente o conteúdo do grafo em uma explicação Markdown, com matemática renderizada em KaTeX.

As execuções não dependem de sessão ou estado global da aplicação: cada solicitação cria um registro `Graph` e os nós e arestas são associados ao ID desse registro. A conexão SSE é transitória; o grafo continua disponível pela API após a execução. O stream não tem mecanismo de retomada após desconexão do cliente ou reinício do processo.

## Configuração e execução

Requisitos: Python compatível com as dependências em `requirements.txt`, credenciais de Ollama e acesso ao AXLE. Crie um `.env` com:

```dotenv
SECRET_KEY=uma-chave-local
OLLAMA_API_KEY=sua-chave-ollama
DATABASE_URL=sqlite:///app.db
CREATIVE_MODEL=gemma4:31b-cloud
WRITER_MODEL=gemma4:31b-cloud
```

Instale as dependências e inicie o Flask:

```bash
pip install -r requirements.txt
flask --app app:create_app run --debug
```

Abra `http://127.0.0.1:5000/` para usar a interface. Ela carrega KaTeX e as fontes do Google Fonts por CDN; a API e o servidor Flask continuam locais.

## Interface web

- O formulário inicia uma execução com a pergunta, número de grafos, gerações e nós por lote. Os limites são, respectivamente, 1–5 grafos, 1–20 gerações e 1–10 nós.
- Os eventos recebidos atualizam o estado da execução e o grafo no canvas. O canvas permite arrastar nós, mover a área e controlar o zoom; selecionar um nó abre sua descrição.
- O seletor carrega grafos anteriores. O botão Writer solicita uma explicação em streaming e renderiza `$...$` e `$$...$$` com KaTeX.

## API

As respostas REST convencionais usam `{ "success": true, "data": ... }`. Os dois endpoints de stream retornam `text/event-stream`; cada evento contém JSON na linha `data:`.

| Método e rota | Uso |
| --- | --- |
| `GET /` | Interface web |
| `POST /agents/reasoning` | Inicia raciocínio e transmite eventos SSE |
| `POST /agents/` | Alias para o stream de raciocínio |
| `POST /agents/writer` | Retorna a síntese completa do Writer como JSON |
| `POST /agents/writer/stream` | Transmite a síntese do Writer em eventos SSE |
| `GET /nodes/graphs` | Lista IDs, tarefas e contagens de nós/arestas |
| `GET /nodes/graph/<graph_id>` | Retorna a tarefa, nós e arestas de um grafo |
| `DELETE /nodes/graphs/<graph_id>` | Exclui o registro do grafo, nós e arestas |
| `GET /nodes?id=<graph_id>` | Lista os nós de um grafo |
| `GET /nodes/graph?id=<graph_id>` | Lista as arestas de um grafo |
| `GET /nodes/<node_id>` | Retorna um nó |
| `POST /nodes/` | Cria um nó |
| `PATCH /nodes/graph` | Cria ou atualiza uma aresta |
| `DELETE /nodes/graph/clear?id=<graph_id>` | Limpa os nós e arestas sem excluir o registro do grafo |
| `DELETE /nodes/graph` | Exclui uma aresta e sua reversa, se houver |

A exclusão completa de um grafo também está disponível no explorador da interface. É permanente e requer confirmação.

### Iniciar raciocínio

```http
POST /agents/reasoning
Content-Type: application/json
```

```json
{
	"task": "Quais condições implicam que uma função contínua seja uniformemente contínua?",
	"n_graphs": 1,
	"generations": 2,
	"new_nodes": 3
}
```

O stream emite `start` com o ID alocado; `progress` antes de cada tentativa; um evento `batch` por lote de conexões verificadas; `graph` com o snapshot persistido ao final de cada geração; e `complete` com o ID final. Durante chamadas longas, envia comentários SSE `: keep-alive` a cada 10 segundos para evitar que conexões ociosas sejam encerradas. Falhas são comunicadas como evento `error` com `message`.

### Gerar uma síntese

```http
POST /agents/writer/stream
Content-Type: application/json

{"graph_id": 1}
```

Cada evento `delta` contém um campo `text` com o próximo trecho; `done` encerra a síntese e `error` informa uma falha. Para receber o texto completo em uma única resposta JSON, use `POST /agents/writer` com o mesmo payload.

## Modelos e persistência

- `Graph` representa uma execução e guarda a tarefa original.
- `Node` guarda proposições, descrição e marcação da afirmação primária.
- `Edge` liga dois nós e registra relação (`uni` ou `bi`), descrição e penalidade.
- `CREATIVE_MODEL` e `WRITER_MODEL` configuram os modelos Ollama separadamente.
- A aplicação cria as tabelas ausentes na inicialização; use as migrações em `migrations/` para evoluir um banco existente.

O Creative deve retornar um objeto JSON com `connections`; cada item contém `a`, `b`, `relation` e `lean.formal_statement`/`lean.content`. IDs novos são remapeados para os IDs persistidos, e conexões só são salvas depois de verificadas pelo AXLE. O Writer não deve afirmar resultados que não estejam representados no grafo.

Antes de persistir cada geração, nós com labels equivalentes são consolidados: normalização Unicode, espaços repetidos e notação matemática equivalente (por exemplo, `\\neq` e `≠`) apontam para um único nó. As arestas são remapeadas para o nó canônico; autoarestas e arestas repetidas resultantes da consolidação são descartadas. Essa regra não depende dos penalties.

## AXLE

O AXLE verifica as tentativas Lean antes da persistência de conexões. A execução requer credenciais e disponibilidade do serviço AXLE. A resposta da ferramenta de verificação é usada pelo agente para registrar erros e tentar outro lote.

