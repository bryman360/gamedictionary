import uuid

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from db import words_db

blp = Blueprint("Words", __name__, description="Blueprint for /word endpoints")


@blp.route("/word/<string:word_id>")
class Word(MethodView):
    def get(self, word_id: str):
        try:
            return {"word_id": word_id, **words_db[word_id]}
        except KeyError:
            abort(404, message=f"Word with ID {word_id} not found.")

    def put(self, word_id: str):
        request_data = request.get_json()
        if (
            "word" not in request_data or
            "definition" not in request_data or
            "example" not in request_data
        ):
            abort(400, message="Bad request. Ensure 'word', 'definition', and 'example' are included in JSON payload.")
        try:
            word = words_db[word_id]
            word_update = {
                "word": request_data["word"],
                "definition": request_data["definition"],
                "example": request_data["example"],
            }
            word |= word_update
            return {"word_id": word_id, **word}
        except KeyError:
            abort(404, message=f"No word with ID {word_id} found.")
    
    def delete(self, word_id:str):
        try:
            del words_db[word_id]
            return {"message": f"Word with ID {word_id} deleted"}
        except KeyError:
            abort(404, message=f"Word with ID {word_id} not found.")


@blp.route("/word")
class WordAdd(MethodView):
    def get(self):
        return words_db
    
    def post(self):
        request_data = request.get_json()
        if (
            "word" not in request_data or
            "definition" not in request_data or
            "example" not in request_data
        ):
            abort(400, message="Bad request. Ensure 'word', 'definition', and 'example' are included in JSON payload.")

        word_id = uuid.uuid4().hex
        new_word_post = {
            "word": request_data["word"],
            "definition": request_data["definition"],
            "example": request_data["example"],
            "author_id": 1,
            "published": False
        }

        words_db[word_id] = new_word_post
        return {"word_id": word_id, **new_word_post}, 201
