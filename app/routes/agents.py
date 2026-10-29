from flask import Blueprint
from ..controllers.ai_agents import stream_reasoning, stream_writer, write_graph

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
