import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api
from flask_mail import Mail
from dotenv import load_dotenv

from resources.game import blp as GameBlueprint
from resources.word import blp as WordBlueprint
from resources.user import blp as UserBlueprint
from resources.flag import blp as FlagBlueprint
from resources.utils import blp as UtilBlueprint
from blocklist import BLOCKLIST
from db import db

import models


def create_app(db_url=None):
    load_dotenv()



    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['API_TITLE'] = 'Game Dict REST API'
    app.config['API_VERSION'] = 'v1'
    app.config['OPENAPI_VERSION'] = '3.0.3'
    app.config['OPENAPI_URL_PREFIX'] = '/'
    app.config['OPENAPI_SWAGGER_UI_PATH'] = '/swagger-ui'
    app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or os.getenv('DATABASE_URL', 'sqlite:///data.db')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token_cookie'
    app.config['JWT_COOKIE_DOMAIN'] = os.getenv('BASE_DOMAIN')
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = os.getenv('SEND_EMAIL')
    app.config['MAIL_PASSWORD'] = os.getenv('SEND_EMAIL_PASSWORD')
    app.config['MAIL_USE_TLS'] = True

    with open('access.txt', 'r') as cred:
        os.environ['IGDB_ACCESS_TOKEN'] = cred.read()


    db.init_app(app)
    migrate = Migrate(app, db)
    api = Api(app)
    mail = Mail(app)
    jwt = JWTManager(app)


    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        additional_claims = {}
        user_roles = models.RoleModel.query.filter_by(user_id=identity).first()
        if user_roles and user_roles.admin == True:
            additional_claims['is_admin'] = True
        return additional_claims

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    'message': 'Access token expired.',
                    'error': 'token_expired'
                }
            ),
            401
        )
    
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload['jti'] in BLOCKLIST
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    'message': 'The token has been revoked.',
                    'error': 'token_revoked'
                }
            )
        )
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    'message': 'Request does not contain an access token.',
                    'error': 'authorization_required'    
                }
            ),
            401
        )
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    'message': 'The token is not fresh.',
                    'error': 'token_not_fresh'
                }
            )
        )

    # @app.before_request
    # def create_tables():
    #     app.before_request_funcs[None].remove(create_tables)
    #     db.create_all()

    api.register_blueprint(GameBlueprint)
    api.register_blueprint(WordBlueprint)
    app.register_blueprint(UserBlueprint)
    app.register_blueprint(FlagBlueprint)
    app.register_blueprint(UtilBlueprint)

    return app
