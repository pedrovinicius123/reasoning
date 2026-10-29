from flask import Blueprint, render_template, jsonify
from ..utils.response import error_response
from ..models.graph import Graph
from ..controllers.ai_agents import interact_with_graph, start_interact_with_graph_thread, generate_essay_step


bp_agents = Blueprint("agents", __name__, url_prefix="/agents")

@bp_agents.route("/", methods=["POST"])
def start_creative_generation():
    try:
        return interact_with_graph()
    except Exception as e:
        return error_response(str(e))

@bp_agents.route("/reasoning", methods=["POST"])
async def reasoning():
    try:
        response = await start_interact_with_graph_thread()
        return response
    except Exception as e:
        return error_response(str(e))

@bp_agents.route("/writer/<int:graph_id>", methods=["GET"])
def writer_page(graph_id:int):
    try:
        graph = Graph.query.filter_by(id=graph_id).first()
        print(graph.nodes)
        if not graph:
            return error_response("Graph not found", 404)
        return render_template("writer.html", graph=graph)
    except Exception as e:
        return error_response(str(e))

@bp_agents.route("/writer/<int:graph_id>/generate", methods=["POST"])
async def generate_writer_step(graph_id):
    try:
        updated_essay = await generate_essay_step(graph_id)
        return jsonify({"essay": updated_essay})
    except Exception as e:
        return error_response(str(e))
