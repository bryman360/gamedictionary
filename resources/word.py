from datetime import datetime
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import WordModel, GameModel
from schemas import WordSchema, WordUpdateSchema, GameSchema

blp = Blueprint("Words", __name__, description="Blueprint for /word endpoints")


@blp.route("/word/<string:word_id>")
class Word(MethodView):
    @blp.response(200, WordSchema)
    def get(self, word_id: int):
        return WordModel.query.get_or_404(word_id)

    @blp.arguments(WordUpdateSchema)
    @blp.response(200, WordSchema)
    def put(self, request_payload: dict, word_id: int):
        word = WordModel.query.get(word_id)
        if word:
            word.word = request_payload['word'] if 'word' in request_payload else word.word
            word.definition = request_payload['definition'] if 'definition' in request_payload else word.word
            word.example = request_payload['example'] if 'example' in request_payload else word.word
        else:
            word = WordModel(**request_payload)
            word.submit_datetime = datetime.now()
            word.published = False

        try:
            db.session.add(word)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message="Could not save word to database.")
    
    @blp.response(200, WordSchema)
    def delete(self, word_id: int):
        word = WordModel.query.get_or_404(word_id)
        try:
            db.session.delete(word)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message=f"Word with ID {word_id} could not be deleted from database.")


@blp.route("/word")
class WordAdd(MethodView):
    @blp.response(200, WordSchema(many=True))
    def get(self):
        return WordModel.query.all()
    
    @blp.arguments(WordSchema)
    @blp.response(201, WordSchema)
    def post(self, request_payload: dict):
        word = WordModel(**request_payload)
        word.submit_datetime = datetime.now()
        word.published = False

        try:
            db.session.add(word)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message="Unable to save word to database.")


@blp.route("/word/<int:word_id>/game")
class WordGamesList(MethodView):
    @blp.response(200, GameSchema(many=True))
    def get(self, word_id: int):
        word = WordModel.query.get_or_404(word_id)
        if word.games:
            return word.games
        return []
