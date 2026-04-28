from app import create_app
from app.utils.networkx_parser import NetworkxParserManager

app = create_app()
if __name__ == '__main__':
    with app.app_context():
        net = NetworkxParserManager("Solve P vs NP", 2)

