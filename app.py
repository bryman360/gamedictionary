import os

from flask import Flask
from flask_smorest import Api

from resources.game import blp as GameBlueprint
from resources.word import blp as WordBlueprint
from db import db

import models


def create_app(db_url=None):
    app = Flask(__name__)

    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['API_TITLE'] = "Game Dict REST API"
    app.config['API_VERSION'] = "v1"
    app.config['OPENAPI_VERSION'] = "3.0.3"
    app.config['OPENAPI_URL_PREFIX'] = "/"
    app.config['OPENAPI_SWAGGER_UI_PATH'] = "/swagger-ui"
    app.config['OPENAPI_SWAGGER_UI_URL'] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or os.getenv('DATABASE_URL', 'sqlite:///data.db')

    db.init_app(app)
    api = Api(app)

    @app.before_request
    def create_tables():
        app.before_request_funcs[None].remove(create_tables)
        db.create_all()

    api.register_blueprint(GameBlueprint)
    api.register_blueprint(WordBlueprint)

    return app
