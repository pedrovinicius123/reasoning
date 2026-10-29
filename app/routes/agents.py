from flask import Blueprint, jsonify, render_template
from ..controllers.ai_agents import (
    generate_essay_step,
    stream_reasoning,
    stream_writer,
    write_graph,
)
from ..models.graph import Graph

bp_agents = Blueprint("agents", __name__, url_prefix="/agents")

@bp_agents.route("/", methods=["POST"])
def start_creative_generation():
    return stream_reasoning()

@bp_agents.route("/reasoning", methods=["POST"])
def reasoning():
    return stream_reasoning()

@bp_agents.route("/writer", methods=["POST"])
def writer():
    return write_graph()

@bp_agents.route("/writer/stream", methods=["POST"])
def writer_stream():
    return stream_writer()

@bp_agents.route("/writer/<int:graph_id>", methods=["GET"])
def writer_page(graph_id):
    graph = Graph.query.get_or_404(graph_id)
    return render_template("writer.html", graph=graph)

@bp_agents.route("/writer/<int:graph_id>/generate", methods=["POST"])
def generate_writer_step(graph_id):
    essay = generate_essay_step(graph_id)
    return jsonify({"essay": essay})
