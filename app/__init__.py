from .extensions import db, migrate, m
from .utils.response import error_response
from .routes.nodes import bp_nodes
from .routes.agents import bp_agents
from werkzeug.exceptions import NotFound
from marshmallow import ValidationError
from flask import Flask
from .config import Config

def create_app():
    # Configurations
    app = Flask(__name__)
    app.config.from_object(Config)

    # Adding extensions
    db.init_app(app)
    migrate.init_app(app, db)
    m.init_app(app)

    with app.app_context():
        db.create_all()

    #Error handlers
    @app.errorhandler(NotFound)
    def not_found(err):
        return error_response(err, 404)
    
    @app.errorhandler(ValidationError)
    def validation_error(err):
        return error_response(err, 400)
    
    @app.errorhandler(500)
    def internal_error(err):
        return error_response(err, 500)
    
    # Adding blueprints 
    app.register_blueprint(bp_nodes)
    app.register_blueprint(bp_agents)
    return app
