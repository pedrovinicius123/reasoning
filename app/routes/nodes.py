from flask import Blueprint
from ..controllers.nodes import list_all_nodes, list_all_edges, get_nid, add_edge, add_node

# BLUEPRINT
bp_nodes = Blueprint("nodes", __name__, url_prefix="/nodes")

# ROUTES
@bp_nodes.route("/", methods=["GET"])
def get_nodes():
    return list_all_nodes()

@bp_nodes.route("/graph", methods=["GET"])
def get_graph():
    return list_all_edges()

@bp_nodes.route("/<int:id>", methods=["GET"])
def get_node_id(id:int):
    return get_nid(id)

@bp_nodes.route("/graph", methods=["PATCH"])
def add_edg():
    return add_edge()

@bp_nodes.route("/", methods=["POST"])
def add_nodes():
    return add_node()
