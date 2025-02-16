from flask.views import MethodView
from flask_jwt_extended import create_access_token
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import SQLAlchemyError


from db import db
from models import UserModel
from schemas import UserSchema, UserUpdateSchema


blp = Blueprint("Users", __name__, description="Blueprint for user operations")


@blp.route("/register")
class UserRegistration(MethodView):
    @blp.arguments(UserSchema)
    def post(self, request_payload):
        if UserModel.query.filter(UserModel.username == request_payload['username']).first():
            abort(409, message="A user with that username already exists.")
        hashed_password = pbkdf2_sha256.hash(request_payload['password'])

        user = UserModel(username=request_payload["username"], password=hashed_password)

        try:
            db.session.add(user)
            db.session.commit()
            return {"message": "User successfully registered."}, 201
        except SQLAlchemyError:
            abort(500, message="Unable to save user to database.")


@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id: int):
        return UserModel.query.get_or_404(user_id)
    
    @blp.arguments(UserUpdateSchema)
    def put(self, request_payload, user_id: int):
        user = UserModel.query.get_or_404(user_id)
        
        if not user:
            user = UserModel(**request_payload)
        else:
            user.password = pbkdf2_sha256.hash(request_payload['password']) if 'password' in request_payload else user.password
            if 'username' in request_payload:
                if UserModel.query.filter(UserModel.username == request_payload['username']).first():
                    abort(409, message="A user with that username already exists.")
                else:
                    user.username = request_payload['username']

        try:
            db.session.add(user)
            db.session.commit()
            return {"message": "User successfully updated."}, 200
        except SQLAlchemyError:
            abort(500, message="Unable to update user in database.")


    
    @blp.response(200, UserSchema)
    def delete(self, user_id: int):
        user = UserModel.query.get_or_404(user_id)

        try:
            db.session.delete(user)
            db.session.commit(user)
        except SQLAlchemyError:
            abort(500, message="Unable to delete user from database.")


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, request_payload):
        user = UserModel.query.filter(UserModel.username == request_payload['username']).first()
        if user and pbkdf2_sha256.verify(request_payload['password'], user.password):
            access_token = create_access_token(identity=user.user_id)
            return {"access_token": access_token}
        abort(401, message="Invalid login credentials.")