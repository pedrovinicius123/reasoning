from app import create_app
from app.utils.networkx_parser import NetworkxParserManger

app = create_app()
if __name__ == "__main__":
    # TESTING!
    with app.app_context():
        manager = NetworkxParserManger()
        manager.dump_best()
