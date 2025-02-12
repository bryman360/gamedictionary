import uuid

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas import GameSchema, GameUpdateSchema
from db import games_db

blp = Blueprint("Games", __name__, description="Blueprint for /game endpoints")


@blp.route("/game/<string:game_id>")
class Game(MethodView):
    @blp.response(200, GameSchema)
    def get(self, game_id: str):
        try:
            return games_db[game_id]
        except KeyError:
            abort(404, message=f"Game with ID {game_id} not found.")

    @blp.arguments(GameUpdateSchema)
    @blp.response(201, GameSchema)
    def put(self, game_update_data, game_id: str):
        try:
            game = games_db[game_id]
            game |= game_update_data
            return game
        except KeyError:
            abort(404, message=f"No game with ID {game_id} found.")

    @blp.response(200, GameSchema)
    def delete(self, game_id: str):
        try:
            game = games_db[game_id]
            del games_db[game_id]
            return game
        except KeyError:
            abort(404, message=f"Game with ID {game_id} not found.")


@blp.route("/game")
class GameList(MethodView):
    @blp.response(200, GameSchema(many=True))
    def get(self):
        return games_db.values()

    @blp.arguments(GameSchema)
    @blp.response(201, GameSchema)
    def post(self, game_data):
        game_id = uuid.uuid4().hex

        games_db[game_id] = {"game_id": game_id, **game_data}
        return {"game_id": game_id, **game_data}, 201
