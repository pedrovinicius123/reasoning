from .agent import Agent
from ...extensions import client
from ...config import Config
import json


def _escape_invalid_json_string_escapes(payload: str) -> str:
  repaired = []
  in_string = False
  index = 0

  while index < len(payload):
    character = payload[index]
    if not in_string:
      repaired.append(character)
      if character == '"':
        in_string = True
      index += 1
      continue

    if character == '"':
      repaired.append(character)
      in_string = False
      index += 1
      continue

    if character != "\\":
      repaired.append(character)
      index += 1
      continue

    if index + 1 >= len(payload):
      repaired.append("\\\\")
      index += 1
      continue

    escaped = payload[index + 1]
    if escaped in '"\\/bfnrt':
      repaired.extend((character, escaped))
      index += 2
      continue

    if escaped == "u" and index + 5 < len(payload):
      unicode_digits = payload[index + 2:index + 6]
      if all(digit in "0123456789abcdefABCDEF" for digit in unicode_digits):
        repaired.append(payload[index:index + 6])
        index += 6
        continue

    repaired.append("\\\\")
    index += 1

  return "".join(repaired)


def _limpar_formal_statement(stmt: str) -> str:
    # Remove `;` que não estejam dentro de um bloco `by ... ; ...`
    # Estratégia conservadora: remove `;` no final de linha ou seguido de espaço/quebra,
    # fora de parênteses de táticas.
    linhas = []
    for linha in stmt.splitlines():
        linha = linha.rstrip()
        if linha.endswith(";"):
            linha = linha[:-1].rstrip()  # remove o `;` final
        linhas.append(linha)
    return "\n".join(linhas).strip()


class CreativeAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", Config.CREATIVE_MODEL)
        self.past_errors = []

    async def interact(self, new_nodes, graph):
        prompt = f"""
You are a Lean 4/Mathlib formalization expert. Your task is to propose {new_nodes} new nodes for an existing mathematical knowledge graph, together with their labels, descriptions, penalties, and connections to existing nodes.

### Graph context
!TASK! {self.task}

Existing nodes and edges (if any) are provided below.  
If the graph is empty, create {new_nodes} initial nodes and connect them among themselves.
The first node must be an afirmation about the task provided (for example, for P vs NP, it must be P /neq NP or P = NP)
Every node coming from it must be also a logical affirmation
Every new node MUST be connected to at least one existing node (or to another new node if the graph is empty).  
Do NOT introduce concepts that are disconnected from the existing graph.
Node ids must be integers. Reuse an existing id only for the same existing node; use a distinct id for every new node.
Before adding a proposition, compare its label with existing nodes and reuse the existing node instead of repeating it. Do not propose two nodes with the same label in one response.


### Mathematical rigor
- Use ONLY well-established theorems and lemmas. No conjectures.
- For each connection, state the mathematical relation (implication: `uni`, or equivalence: `bi`).
- Explain how the new node affects the existing node and vice versa.

### Lean 4 code requirements
- The `lean` field of each connection MUST contain two subfields: `formal_statement` and `content`.
- `formal_statement`: a self-contained Lean 4 declaration that ends exactly with `:= by sorry`.
- `content`: a Lean 4 proof attempt that could verify the connection (it may contain `sorry` if needed).
- Define EVERY variable explicitly in the Lean code, e.g. `(P : Set α)`, `(L : α)`, `(DTM : Type)`.
- Import every library needed, e.g. `import Mathlib`.
- NEVER use dot notation (.contains, .length, etc.) on variables that are functions or predicates. For a set represented as String → Prop, use x ∈ L or L x. Dot notation is only valid for fields of structures (e.g., s.length when s : String), not for functions.
- Use Lean 4 syntax only.
- Do not Use Mathlib reserved words from Lean 4 {{
    "Language", "Set", "Type", "Bool", "Nat", "Int", "String", "List",
    "Finset", "Prop", "Function", "Option", "Prod", "Sum", "Polynomial",
    "Matrix", "Group", "Ring", "Field", "Vector", "Array",
}}
- The `content` field must be a COMPLETE and SELF-CONTAINED Lean 4 file, identical to the `formal_statement` but with the actual proof instead of `:= by sorry`. In other words:
  .  Start with `import Mathlib` (and any other necessary imports).
  .  Repeat the theorem declaration: `theorem <name> <parameters> : <statement> := by`.
  . Provide the actual proof tactics.
  . DO NOT use `sorry` within the `content` (unless the theorem is included in `permitted_sorries`).
  . DO NOT omit the theorem declaration — standalone tactics (such as `intros`, `cases`, etc.) without the `theorem ... := by` structure will be rejected by Lean."
### Output format — STRICT
Return **ONLY** a JSON object with the following shape, with **no text outside the JSON**:

{{
  "connections": [
    {{
      "a": {{
        "id": "integer",
        "label": "string",
        "desc": "string",
        "penalty": 0.0
      }},
      "b": {{
        "id": "integer",
        "label": "string",
        "desc": "string",
        "penalty": 0.0
      }},
      "desc": "string",
      "lean": {{
        "formal_statement": "string",
        "content": "string"
    }},
      "penalty": 0.0,
      "relation": "uni|bi"
    }}
  ]
}}

### Past runtime errors
{self.past_errors}

### Final rules
- If the graph already contains a cycle involving the primary node, return an empty JSON object: `{{}}`.
- Do NOT use conjectures.
- Return valid JSON: escape every backslash in string values as `\\\\`. For example, encode `NP \\ P` as `"NP \\\\ P"`.
- Encode line breaks in string values as `\\n` and escape quotation marks inside strings. Never emit invalid escapes such as `\\ ` or `\\P`.
- Write the response clearly and extensively **inside the JSON fields**, but do not add prose outside the JSON.
- Follow the JSON schema exactly. Any deviation will break the downstream system.
"""

        print("Before bug")
        prompt += self.prompt_graph(graph)
        print("Prompt built, sending to model...")
        response = client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            think=True,
            options={
                "temperature": 0.5,
            },
        ).message.content
        response = response.replace("```json", "").replace("```", "").strip()
        print(response)
        try:
            try:
                results = json.loads(response)
            except json.JSONDecodeError:
                repaired_response = _escape_invalid_json_string_escapes(response)
                if repaired_response == response:
                    raise
                results = json.loads(repaired_response)
            if results == {}:
                return results
            if not isinstance(results, dict) or not isinstance(results.get("connections"), list):
                raise ValueError("Expected an object with a connections array")
            for result in results["connections"]:
                if not isinstance(result, dict) or not all(key in result for key in ("a", "b", "lean", "relation")):
                    raise ValueError("Each connection must include a, b, lean, and relation")
                if result["relation"] not in ("uni", "bi"):
                    raise ValueError("Connection relation must be uni or bi")
                for node in (result["a"], result["b"]):
                    if (
                        not isinstance(node, dict)
                        or not isinstance(node.get("id"), int)
                        or isinstance(node.get("id"), bool)
                    ):
                        raise ValueError("Each node must have an integer id")
                    if not isinstance(node.get("label"), str) or not isinstance(node.get("desc"), str):
                        raise ValueError("Each node must have a label and description")
                if not isinstance(result.get("desc"), str):
                    raise ValueError("Each connection must have a description")
                if not isinstance(result.get("penalty"), (int, float)) or isinstance(result.get("penalty"), bool):
                    raise ValueError("Each connection must have a numeric penalty")
                lean = result.get("lean")
                if not isinstance(lean, dict) or not all(
                    isinstance(lean.get(key), str) for key in ("formal_statement", "content")
                ):
                    raise ValueError("Lean formal_statement and content are required")

            return results
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from model: {response}") from e
        except Exception as e:
            raise ValueError(f"Invalid response format: {e}") from e
