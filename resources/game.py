import uuid

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from db import games_db

blp = Blueprint("Games", __name__, description="Blueprint for /game endpoints")


@blp.route("/game/<string:game_id>")
class Game(MethodView):
    def get(self, game_id: str):
        try:
            return {"game_id": game_id, **games_db[game_id]}
        except KeyError:
            abort(404, message=f"Game with ID {game_id} not found.")

    def put(self, game_id: str):
        request_data = request.get_json()
        if (
            "game_name" not in request_data
        ):
            abort(400, message="Bad request. Ensure 'game_name' is included in JSON payload.")
        try:
            game = games_db[game_id]
            game_update = {
                "game_name": request_data["game_name"]
            }
            game |= game_update
            return {"game_id": game_id, **game}
        except KeyError:
            abort(404, message=f"No game with ID {game_id} found.")

    def delete(self, game_id: str):
        try:
            del games_db[game_id]
            return {"message": f"Game with ID {game_id} deleted"}
        except KeyError:
            abort(404, message=f"Game with ID {game_id} not found.")


@blp.route("/game")
class GameList(MethodView):
    def get(self):
        return games_db

    def post(self):
        request_data = request.get_json()
        if (
            "game_name" not in request_data
        ):
            abort(400, message="Bad request. Ensure 'game_name' is in the payload.")

        game_id = uuid.uuid4().hex
        new_word_post = {
            "game_name": request_data["game_name"]
        }

        games_db[game_id] = new_word_post
        return {"game_id": game_id, **new_word_post}, 201
