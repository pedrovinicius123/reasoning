from flask import Blueprint, request
from ..utils.response import successful_response, error_response
from ..controllers.ai_agents import interact_with_graph, develop_graph

bp_agents = Blueprint("agents", __name__, url_prefix="/agents")

@bp_agents.route("/", methods=["POST"])
def start_creative_generation():
    return interact_with_graph()

@bp_agents.route("/reasoning", methods=["POST"])
def reasoning():
    try:
        if not request.is_json:
            return error_response("Request must be JSON", 400)
        develop_graph()
        return successful_response({"message": "Development started"}, 202)
    except Exception as e:
        return error_response(str(e), 500)
