from flask import Blueprint
from ..controllers.ai_agents import interact_with_graph, analyse_graph

bp_agents = Blueprint("agents", __name__, url_prefix="/agents")

@bp_agents.route("/", methods=["POST"])
def start_creative_generation():
    return interact_with_graph()

@bp_agents.route("/", methods=["GET"])
def parse_graph():
    return analyse_graph()
