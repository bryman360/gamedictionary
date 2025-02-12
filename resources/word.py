import uuid

from datetime import datetime
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas import WordSchema, WordUpdateSchema
from db import words_db

blp = Blueprint("Words", __name__, description="Blueprint for /word endpoints")


@blp.route("/word/<string:word_id>")
class Word(MethodView):
    @blp.response(200, WordSchema)
    def get(self, word_id: str):
        try:
            return words_db[word_id]
        except KeyError:
            abort(404, message=f"Word with ID {word_id} not found.")

    @blp.arguments(WordUpdateSchema)
    @blp.response(200, WordSchema)
    def put(self, word_update_data, word_id: str):
        try:
            word = words_db[word_id]
            word |= word_update_data
            return word
        except KeyError:
            abort(404, message=f"No word with ID {word_id} found.")
    
    @blp.response(200, WordSchema)
    def delete(self, word_id:str):
        try:
            word = words_db[word_id]
            del words_db[word_id]
            return word
        except KeyError:
            abort(404, message=f"Word with ID {word_id} not found.")


@blp.route("/word")
class WordAdd(MethodView):
    @blp.response(200, WordSchema(many=True))
    def get(self):
        return words_db.values()
    
    @blp.arguments(WordSchema)
    @blp.response(201, WordSchema)
    def post(self, word_data):

        word_id = uuid.uuid4().hex
        new_word_post = {
            "word_id": word_id,
            "word": word_data["word"],
            "definition": word_data["definition"],
            "example": word_data["example"],
            "author_id": word_data['author_id'],
            "published": False,
            "submit_datetime": datetime.now()
        }

        words_db[word_id] = new_word_post
        return {"word_id": word_id, **new_word_post}, 201
