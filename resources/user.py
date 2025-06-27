import os

from datetime import timedelta
from google.oauth2 import id_token
from google.auth.transport import requests as google_req
from flask.views import MethodView
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required, create_refresh_token
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import SQLAlchemyError


from blocklist import BLOCKLIST
from db import db
from models import UserModel
from schemas import UserSchema, UserUpdateSchema, LoginSchema


blp = Blueprint('Users', __name__, description='Blueprint for user operations')

access_token_expiration_time = timedelta(minutes=10)
refresh_token_expiration_time = timedelta(days=30)


@blp.route('/register')
class UserRegistration(MethodView):
    @blp.arguments(UserSchema)
    def post(self, request_payload):
        user_lookup = UserModel.query.filter(UserModel.username == request_payload['username']).first()
        if user_lookup and user_lookup.is_active:
            abort(409, message='A user with that username already exists.')
        hashed_password = pbkdf2_sha256.hash(request_payload['password'])

        user = UserModel(username=request_payload['username'], password=hashed_password)
        user.is_active = True

        try:
            db.session.add(user)
            db.session.commit()
            return {
                'message': 'User successfully registered.',
                'access_token': create_access_token(identity=str(user.user_id), fresh=True),
                'refresh_token': create_refresh_token(identity=str(user.user_id))
            }, 201
        except SQLAlchemyError:
            abort(500, message='Unable to save user to database.')


@blp.route('/users/<int:user_id>')
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id: int):
        return UserModel.query.get_or_404(user_id)
    
    @jwt_required(fresh=True)
    @blp.arguments(UserUpdateSchema)
    def put(self, request_payload, user_id: int):
        jwt = get_jwt()
        current_user = get_jwt_identity()
        if not jwt.get('is_admin') and not current_user == str(user_id):
            abort(403, message=f'Permission denied, user id does not match account id')

        user = UserModel.query.get_or_404(user_id)
        status_code = 202
        
        if not user:
            user = UserModel(**request_payload)
            status_code = 201
        else:
            user.password = pbkdf2_sha256.hash(request_payload['password']) if 'password' in request_payload else user.password
            if 'username' in request_payload:
                if UserModel.query.filter(UserModel.username == request_payload['username']).first():
                    abort(409, message='A user with that username already exists.')
                else:
                    user.username = request_payload['username']

        try:
            db.session.add(user)
            db.session.commit()
            return {'message': 'User successfully updated.'}, status_code
        except SQLAlchemyError:
            abort(500, message='Unable to update user in database.')


    # TODO: Rather than actually delete, just flag it for deletion later so it's not a true delete
    @jwt_required(fresh=True)
    @blp.response(204)
    def delete(self, user_id: int):
        jwt = get_jwt()
        current_user = get_jwt_identity()
        if not jwt.get('is_admin') and not current_user == str(user_id):
            abort(403, message='Permission denied, user id does not match account id.')

        user = UserModel.query.get_or_404(user_id)
        user.is_active = False

        try:
            db.session.add(user)
            db.session.commit()
            #TODO: Expire token.
            return {}
        except SQLAlchemyError:
            abort(500, message='Unable to delete user from database.')


@blp.route('/login')
class UserLogin(MethodView):
    @blp.arguments(LoginSchema)
    def post(self, request_payload):
        if request_payload['source'] == 'Google':
            try:
                decoded_token = id_token.verify_oauth2_token(request_payload['token'], google_req.Request(), os.getenv('GOOGLE_CLIENT_ID'))
                if decoded_token['iss'] != 'https://accounts.google.com':
                    raise Exception('Error signing in with Google sign-in. Token is not a valid Google OAuth token.')
                user_email = decoded_token['email']

            except Exception as e:
                abort(500, message=e)

        user = UserModel.query.filter(UserModel.email == user_email).first()

        if user and user.is_active:
            access_token = create_access_token(identity=str(user.user_id), fresh=True, expires_delta=access_token_expiration_time)
            refresh_token = create_refresh_token(identity=str(user.user_id), expires_delta=refresh_token_expiration_time)
            try:
                return {
                    'message': 'User successfully logged in.',
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }, 200
            except SQLAlchemyError:
                abort(500, message='Unable to save user to database.')

        elif not user:
            user = UserModel(
                username=user_email,
                email=user_email,
                is_active=True
            )
            try:
                db.session.add(user)
                db.session.commit()
                user = UserModel.query.filter(UserModel.email == user_email).first()
                user_id = user.user_id
                return {
                    'message': 'User successfully registered.',
                    'access_token': create_access_token(identity=str(user.user_id), fresh=True, expires_delta=access_token_expiration_time),
                    'refresh_token': create_refresh_token(identity=str(user_id), expires_delta=refresh_token_expiration_time)
                }, 201
            except SQLAlchemyError:
                abort(500, message='Unable to save user to database.')


@blp.route('/logout')
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jwt = get_jwt()
        jti = jwt.get('jti')
        BLOCKLIST.add(jti)
        return {'message': 'Successfully logged out.'}


# TODO: Change refresh tokens to maybe be server side?
@blp.route('/refresh')
class UserRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=user_id, fresh=False, expires_delta=access_token_expiration_time)
        BLOCKLIST.add(get_jwt()['jti'])
        return {'access_token': new_access_token}