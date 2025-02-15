from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import GameModel, WordModel
from schemas import GameSchema, GameUpdateSchema, WordSchema


blp = Blueprint("Games", __name__, description="Blueprint for /game endpoints")


@blp.route("/game/<int:game_id>")
class Game(MethodView):
    @blp.response(200, GameSchema)
    def get(self, game_id):
        return GameModel.query.get_or_404(game_id)
    
    @blp.arguments(GameUpdateSchema)
    @blp.response(201, GameSchema)
    def put(self, request_payload, game_id):
        game = GameModel.query.get(game_id)
        if game:
            game.game_name = request_payload['game_name']
        else:
            game = GameModel(**request_payload)
        try:
            db.session.add(game)
            db.session.commit()
            return game
        except SQLAlchemyError:
            abort(500, message="Unable to post to SQL database.")

    @blp.response(200, GameSchema)
    def delete(self, game_id: str):
        try:
            game = GameModel.query.get_or_404(game_id)
            db.session.delete(game)
            db.session.commit()
            return game
        except KeyError:
            abort(404, message=f"Game with ID {game_id} not found.")


@blp.route("/game")
class GameList(MethodView):
    @blp.response(200, GameSchema(many=True))
    def get(self):
        return GameModel.query.all()

    @blp.arguments(GameSchema)
    @blp.response(201, GameSchema)
    def post(self, request_payload):
        game = GameModel(**request_payload)
        try:
            db.session.add(game)
            db.session.commit()
            return game
        except SQLAlchemyError:
            abort(500, message="Unable to post to database.")


@blp.route("/game/<int:game_id>/word")
class GameWordsList(MethodView):
    @blp.response(200, WordSchema(many=True))
    def get(self, game_id: int):
        game = GameModel.query.get_or_404(game_id)
        if game.words:
            return game.words
        else:
            return []
    

@blp.route("/game/<int:game_id>/word/<int:word_id>")
class LinkGameToWord(MethodView):
    @blp.response(201, WordSchema)
    def post(self, game_id: int, word_id: int):
        game = GameModel.query.get_or_404(game_id)
        word = WordModel.query.get_or_404(word_id)

        game.words.append(word)
        try:
            db.session.add(game)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message="Unable to link game and word in database.")
    
    @blp.response(200, WordSchema)
    def delete(self, game_id: int, word_id: int):
        game = GameModel.query.get_or_404(game_id)
        word = WordModel.query.get_or_404(word_id)

        game.words.remove(word)
        try:
            db.session.add(game)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message="Unable to delete game and word link in database.")
