const graphSelect = document.querySelector("#graph-select");
const graphSvg = document.querySelector("#graph-svg");
const graphEmpty = document.querySelector("#graph-empty");
const graphSummary = document.querySelector("#graph-summary");
const reasoningForm = document.querySelector("#reasoning-form");
const runStatus = document.querySelector("#run-status");
const runStatusBox = document.querySelector(".run-status");
const writerOutput = document.querySelector("#writer-output");
const writerState = document.querySelector("#writer-state");
const writeButton = document.querySelector("#write-button");
const deleteGraphButton = document.querySelector("#delete-graph");
const eventLog = document.querySelector("#event-log");
const inspector = document.querySelector("#node-inspector");
const SVG_NS = "http://www.w3.org/2000/svg";
let activeGraph = null;
let positions = new Map();
let view = { x: 0, y: 0, width: 900, height: 560 };
let pointerAction = null;

function setRunStatus(text, running = false) {
  runStatus.textContent = text;
  runStatusBox.classList.toggle("running", running);
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.text();
  let data;
  try {
    data = body.trim() ? JSON.parse(body) : null;
  } catch {
    throw new Error(`Resposta inválida da API em ${url} (HTTP ${response.status}, ${response.headers.get("content-type") || "sem Content-Type"})`);
  }
  if (!response.ok || data?.success === false) {
    throw new Error(data?.error_msg || data?.message || `HTTP ${response.status}`);
  }
  if (!data) throw new Error(`Resposta vazia da API em ${url} (HTTP ${response.status})`);
  return data.data;
}

async function loadGraphList(selectedId) {
  const graphs = await api("/nodes/graphs");
  graphSelect.replaceChildren();
  if (!graphs.length) graphSelect.add(new Option("Nenhum grafo", ""));
  for (const graph of graphs) {
    const option = new Option(`#${graph.id} · ${graph.task}`, graph.id);
    graphSelect.add(option);
  }
  const nextId = selectedId ?? (graphs[0] && graphs[0].id);
  if (nextId) {
    graphSelect.value = String(nextId);
    await loadGraph(nextId);
  } else {
    activeGraph = null;
    writeButton.disabled = true;
    renderGraph(null);
  }
}

async function loadGraph(graphId) {
  if (!graphId) return;
  deleteGraphButton.disabled = true;
  try {
    activeGraph = await api(`/nodes/graph/${graphId}`);
    positions = new Map();
    writeButton.disabled = activeGraph.nodes.length === 0;
    deleteGraphButton.disabled = false;
    graphSummary.innerHTML = `<span>GRAFO #${activeGraph.id} · ${escapeHtml(activeGraph.task)}</span><span>${activeGraph.nodes.length} nós · ${activeGraph.edges.length} arestas</span>`;
    renderGraph(activeGraph);
  } catch (error) {
    setRunStatus(error.message);
  }
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  return element;
}

function nodePosition(node, index, count) {
  if (positions.has(String(node.id))) return positions.get(String(node.id));
  const angle = (2 * Math.PI * index / Math.max(count, 1)) - Math.PI / 2;
  const radius = Math.min(205, 85 + count * 8);
  const position = { x: 450 + Math.cos(angle) * radius, y: 278 + Math.sin(angle) * radius };
  positions.set(String(node.id), position);
  return position;
}

function renderGraph(graph) {
  graphSvg.replaceChildren();
  graphSvg.setAttribute("viewBox", `${view.x} ${view.y} ${view.width} ${view.height}`);
  graphEmpty.hidden = Boolean(graph && graph.nodes.length);
  inspector.hidden = true;
  if (!graph || !graph.nodes.length) return;

  const defs = svgElement("defs");
  for (const [id, color] of [["arrow", "#c65e43"], ["arrow-bi", "#77aeb7"]]) {
    const marker = svgElement("marker", {
      id, markerWidth: 8, markerHeight: 8, refX: 6, refY: 3,
      orient: "auto", markerUnits: "strokeWidth",
    });
    marker.append(svgElement("path", { d: "M0,0 L0,6 L7,3 z", fill: color }));
    defs.append(marker);
  }
  graphSvg.append(defs);

  const nodes = graph.nodes;
  const nodeById = new Map(nodes.map((node) => [String(node.id), node]));
  const pointById = new Map(nodes.map((node, index) => [String(node.id), nodePosition(node, index, nodes.length)]));
  const edgeLayer = svgElement("g");
  const drawnBidirectional = new Set();
  for (const edge of graph.edges) {
    const start = pointById.get(String(edge.source));
    const end = pointById.get(String(edge.target));
    if (!start || !end) continue;
    const relation = edge.relation === "bi";
    const pair = [String(edge.source), String(edge.target)].sort().join(":");
    if (relation && drawnBidirectional.has(pair)) continue;
    if (relation) drawnBidirectional.add(pair);
    const line = svgElement("line", {
      x1: start.x, y1: start.y, x2: end.x, y2: end.y,
      class: `edge-line${relation ? " bi" : ""}`,
      "marker-end": relation ? "url(#arrow-bi)" : "url(#arrow)",
    });
    edgeLayer.append(line);
    if (relation) {
      const reverse = svgElement("line", {
        x1: end.x, y1: end.y, x2: start.x, y2: start.y,
        class: "edge-line bi", "marker-end": "url(#arrow-bi)",
      });
      edgeLayer.append(reverse);
    }
    const label = svgElement("text", {
      x: (start.x + end.x) / 2, y: (start.y + end.y) / 2 - 6, class: "edge-label",
    });
    label.textContent = relation ? "⇄" : "→";
    edgeLayer.append(label);
  }
  graphSvg.append(edgeLayer);

  for (const [index, node] of nodes.entries()) {
    const position = pointById.get(String(node.id));
    const group = svgElement("g", { class: "node-group", transform: `translate(${position.x} ${position.y})` });
    const circle = svgElement("circle", {
      r: 34, class: `node-shape${node.is_primary ? " primary" : ""}`,
    });
    const label = svgElement("text", { y: -1, class: "node-label", "text-anchor": "middle" });
    label.textContent = String(node.label || `Nó ${node.id}`).slice(0, 20);
    const id = svgElement("text", { y: 14, class: "node-id", "text-anchor": "middle" });
    id.textContent = `#${node.id}`;
    group.append(circle, label, id);
    group.addEventListener("click", () => showNode(node));
    group.addEventListener("pointerdown", (event) => beginNodeDrag(event, group, node.id));
    graphSvg.append(group);
  }
}

function showNode(node) {
  document.querySelector("#inspector-label").textContent = node.label || `Nó ${node.id}`;
  document.querySelector("#inspector-desc").textContent = node.desc || "Sem descrição.";
  document.querySelector("#inspector-primary").hidden = !node.is_primary;
  inspector.hidden = false;
}

function beginNodeDrag(event, group, nodeId) {
  if (event.button !== 0) return;
  event.stopPropagation();
  group.setPointerCapture(event.pointerId);
  const svgPoint = screenToGraph(event.clientX, event.clientY);
  const transform = group.transform.baseVal.consolidate().matrix;
  pointerAction = { type: "node", nodeId: String(nodeId), group, dx: transform.e - svgPoint.x, dy: transform.f - svgPoint.y };
  showNode(activeGraph.nodes.find((node) => String(node.id) === String(nodeId)) || { id: nodeId });
}

function screenToGraph(clientX, clientY) {
  const rect = graphSvg.getBoundingClientRect();
  return {
    x: view.x + (clientX - rect.left) * view.width / rect.width,
    y: view.y + (clientY - rect.top) * view.height / rect.height,
  };
}

graphSvg.addEventListener("pointerdown", (event) => {
  if (event.target !== graphSvg) return;
  pointerAction = { type: "pan", clientX: event.clientX, clientY: event.clientY, viewX: view.x, viewY: view.y };
  graphSvg.setPointerCapture(event.pointerId);
});
graphSvg.addEventListener("pointermove", (event) => {
  if (!pointerAction) return;
  if (pointerAction.type === "node") {
    const point = screenToGraph(event.clientX, event.clientY);
    const position = { x: point.x + pointerAction.dx, y: point.y + pointerAction.dy };
    positions.set(pointerAction.nodeId, position);
    pointerAction.group.setAttribute("transform", `translate(${position.x} ${position.y})`);
    renderEdgesOnly();
  } else {
    const rect = graphSvg.getBoundingClientRect();
    view.x = pointerAction.viewX - (event.clientX - pointerAction.clientX) * view.width / rect.width;
    view.y = pointerAction.viewY - (event.clientY - pointerAction.clientY) * view.height / rect.height;
    graphSvg.setAttribute("viewBox", `${view.x} ${view.y} ${view.width} ${view.height}`);
  }
});
graphSvg.addEventListener("pointerup", () => { pointerAction = null; });
graphSvg.addEventListener("pointercancel", () => { pointerAction = null; });

function renderEdgesOnly() {
  if (!activeGraph) return;
  const edges = graphSvg.querySelector("g");
  if (!edges) return;
  const [edgeLayer] = [edges];
  edgeLayer.replaceChildren();
  const drawnBidirectional = new Set();
  for (const edge of activeGraph.edges) {
    const start = positions.get(String(edge.source));
    const end = positions.get(String(edge.target));
    if (!start || !end) continue;
    const relation = edge.relation === "bi";
    const pair = [String(edge.source), String(edge.target)].sort().join(":");
    if (relation && drawnBidirectional.has(pair)) continue;
    if (relation) drawnBidirectional.add(pair);
    const line = svgElement("line", {
      x1: start.x, y1: start.y, x2: end.x, y2: end.y,
      class: `edge-line${relation ? " bi" : ""}`,
      "marker-end": relation ? "url(#arrow-bi)" : "url(#arrow)",
    });
    edgeLayer.append(line);
    if (relation) edgeLayer.append(svgElement("line", {
      x1: end.x, y1: end.y, x2: start.x, y2: start.y, class: "edge-line bi", "marker-end": "url(#arrow-bi)",
    }));
  }
  graphSvg.insertBefore(edgeLayer, graphSvg.firstChild);
}

function zoom(factor) {
  const width = Math.max(360, Math.min(1500, view.width * factor));
  const height = width * 560 / 900;
  view.x += (view.width - width) / 2;
  view.y += (view.height - height) / 2;
  view.width = width;
  view.height = height;
  graphSvg.setAttribute("viewBox", `${view.x} ${view.y} ${view.width} ${view.height}`);
}

function parseSseBlock(block) {
  const lines = block.split("\n");
  const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim();
  const data = lines.filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim()).join("\n");
  if (!event || !data) return null;
  try {
    return { event, data: JSON.parse(data) };
  } catch {
    throw new Error(`Evento SSE inválido: ${event}`);
  }
}

async function consumeSse(response, onEvent) {
  if (!response.ok || !response.body) throw new Error(`Falha HTTP ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop();
    for (const block of blocks) {
      const parsed = parseSseBlock(block);
      if (parsed) onEvent(parsed.event, parsed.data);
    }
    if (done) break;
  }
}

reasoningForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = {
    task: document.querySelector("#task").value.trim(),
    n_graphs: Number(document.querySelector("#n-graphs").value),
    generations: Number(document.querySelector("#generations").value),
    new_nodes: Number(document.querySelector("#new-nodes").value),
  };
  setRunStatus("Conectando ao agente Creative…", true);
  eventLog.textContent = "Stream de raciocínio aberto";
  graphSelect.disabled = true;
  let completedGraphId = null;
  try {
    const response = await fetch("/agents/reasoning", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    await consumeSse(response, (name, data) => {
      if (name === "start") {
        setRunStatus(`Grafo #${data.graph_id} iniciado`, true);
        graphSummary.textContent = `Execução em andamento · grafo #${data.graph_id}`;
        activeGraph = { id: data.graph_id, task: data.task, nodes: [], edges: [] };
        renderGraph(activeGraph);
      } else if (name === "progress") {
        setRunStatus(`Geração ${data.generation}, grafo ${data.graph_index}, tentativa ${data.attempt}…`, true);
      } else if (name === "batch") {
        activeGraph = { id: data.graph_id, task: body.task, ...data.graph };
        renderGraph(activeGraph);
        setRunStatus(`Geração ${data.generation}, grafo ${data.graph_index}: ${data.verified_connections} conexões verificadas`, true);
      } else if (name === "graph") {
        activeGraph = { id: data.graph_id, ...data };
        renderGraph(activeGraph);
        graphSummary.textContent = `Grafo #${data.graph_id} · ${data.nodes.length} nós · ${data.edges.length} arestas`;
      } else if (name === "complete") {
        completedGraphId = data.graph_id;
        setRunStatus(`Execução concluída · grafo #${data.graph_id}`);
        eventLog.textContent = `Último grafo criado: #${data.graph_id}`;
      } else if (name === "error") {
        setRunStatus(`Falha: ${data.message}`);
      }
    });
  } catch (error) {
    setRunStatus(`Falha: ${error.message}`);
  } finally {
    graphSelect.disabled = false;
    const selectedGraphId = completedGraphId ?? (Number(graphSelect.value) || undefined);
    await loadGraphList(selectedGraphId).catch((error) => setRunStatus(error.message));
  }
});

writeButton.addEventListener("click", async () => {
  if (!activeGraph) return;
  writerOutput.replaceChildren();
  writerState.textContent = "Writer está compondo…";
  writeButton.disabled = true;
  let output = "";
  try {
    const response = await fetch("/agents/writer/stream", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ graph_id: activeGraph.id }),
    });
    await consumeSse(response, (name, data) => {
      if (name === "delta") {
        output += data.text;
        writerOutput.textContent = output;
      } else if (name === "done") {
        writerState.textContent = "Síntese concluída";
        renderMath();
      } else if (name === "error") {
        writerState.textContent = `Falha: ${data.message}`;
      }
    });
  } catch (error) {
    writerState.textContent = `Falha: ${error.message}`;
  } finally {
    writeButton.disabled = !activeGraph || activeGraph.nodes.length === 0;
  }
});

function renderMath() {
  if (window.renderMathInElement) {
    window.renderMathInElement(writerOutput, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
      ],
      throwOnError: false,
    });
  }
}

graphSelect.addEventListener("change", () => loadGraph(graphSelect.value));
document.querySelector("#refresh-graphs").addEventListener("click", () => loadGraphList(graphSelect.value || undefined));
deleteGraphButton.addEventListener("click", async () => {
  const graphId = Number(graphSelect.value);
  if (!graphId || !window.confirm(`Excluir o grafo #${graphId} e todos os seus nós e arestas? Esta ação não pode ser desfeita.`)) return;

  deleteGraphButton.disabled = true;
  try {
    await api(`/nodes/graphs/${graphId}`, { method: "DELETE" });
    activeGraph = null;
    writerOutput.replaceChildren();
    writerState.textContent = "Aguardando grafo";
    setRunStatus(`Grafo #${graphId} excluído`);
    await loadGraphList();
  } catch (error) {
    deleteGraphButton.disabled = false;
    setRunStatus(`Falha ao excluir: ${error.message}`);
  }
});
document.querySelector("#close-inspector").addEventListener("click", () => { inspector.hidden = true; });
document.querySelector("#zoom-in").addEventListener("click", () => zoom(.82));
document.querySelector("#zoom-out").addEventListener("click", () => zoom(1.22));
document.querySelector("#zoom-reset").addEventListener("click", () => { view = { x: 0, y: 0, width: 900, height: 560 }; renderGraph(activeGraph); });
graphSvg.addEventListener("wheel", (event) => { event.preventDefault(); zoom(event.deltaY < 0 ? .92 : 1.08); }, { passive: false });

loadGraphList().catch((error) => {
  document.querySelector("#connection-status").textContent = "API indisponível";
  setRunStatus(error.message);
});