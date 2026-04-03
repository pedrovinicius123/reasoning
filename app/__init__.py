from .extensions import db, migrate, m
from .utils.response import error_response
from .routes.nodes import bp_nodes
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

    #Error handlers
    @app.errorhandler(NotFound)
    def not_found(err):
        return error_response(err, 404)
    
    @app.errorhandler(ValidationError)
    def validation_error(err):
        return error_response(err, 400)
    
    # Adding blueprints 
    app.register_blueprint(bp_nodes)
    return app
