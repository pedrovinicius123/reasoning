from flask import Blueprint, request, current_app
from ..utils.response import successful_response, error_response
from ..controllers.ai_agents import interact_with_graph, start_interact_with_graph_thread

bp_agents = Blueprint("agents", __name__, url_prefix="/agents")

@bp_agents.route("/", methods=["POST"])
def start_creative_generation():
    return interact_with_graph()

@bp_agents.route("/reasoning", methods=["POST"])
def reasoning():
    with current_app.app_context():
        return start_interact_with_graph_thread()
