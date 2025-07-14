from flask import jsonify
from flask.views import MethodView
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import WordModel, GameModel, GamesWordsModel, GamesWordsLinkUserModel, UserModel
from schemas import WordSchema, GameAndWordLinkSchema

blp = Blueprint('Links', __name__, description='Blueprint for /links specific endpoints')
    

@blp.route('/links')
class LinkGameToWord(MethodView):
    @jwt_required()
    @blp.arguments(GameAndWordLinkSchema)
    @blp.response(201, WordSchema)
    def post(self, request_payload: dict):
        game_id = request_payload['game_id']
        word_id = request_payload['word_id']
        game_word_link = GamesWordsModel.query.filter_by(game_id=game_id, word_id=word_id).first()

        if game_word_link:
            abort(409, message='Link already exists.')

        game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()
        word = WordModel.query.filter_by(word_id=word_id, is_active=True).first_or_404()
        
        game.words.append(word)
        
        try:
            db.session.add(game)
            db.session.flush()
            game_word_link = GamesWordsModel.query.filter_by(game_id=game_id, word_id=word_id).first()
            games_words_link_author = GamesWordsLinkUserModel(game_word_id=game_word_link.game_word_id, user_id=get_jwt_identity())
            db.session.add(games_words_link_author)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message='Unable to link game and word in database.')


@blp.route('/links/<int:game_id>/<int:word_id>')
class LinkGameToWord(MethodView):
    @jwt_required()
    @blp.response(204)
    def delete(self, game_id: int, word_id: int):
        jwt = get_jwt()

        game_word_link = GamesWordsModel.query.filter_by(game_id=game_id, word_id=word_id).first_or_404()
        game_word_link_user = GamesWordsLinkUserModel.query.filter_by(game_word_id=game_word_link.game_word_id, user_id=get_jwt_identity()).first_or_404()

        if not game_word_link_user and not jwt.get('is_admin'):
            abort(401, message='Permission denied to delete game/word link.')

        try:
            db.session.delete(game_word_link_user)
            db.session.delete(game_word_link)
            db.session.commit()
            return {}
        except SQLAlchemyError:
            abort(500, message='Unable to delete game and word link in database.')



    
@blp.route('/links/mylinks')
class MyLinks(MethodView):
    # @jwt_required()
    def get(self):
        # user_id = get_jwt_identity()
        games_words_query = select(
            GamesWordsModel.game_word_id,
            GameModel.game_id,
            GameModel.game_name,
            GameModel.developer,
            WordModel.word_id,
            WordModel.word,
            WordModel.definition,
            WordModel.example,
            WordModel.submit_datetime
        ).join(WordModel, WordModel.word_id == GamesWordsModel.word_id
        ).join(GameModel, GameModel.game_id == GamesWordsModel.game_id
        ).join(GamesWordsLinkUserModel
        ).where(
            GamesWordsLinkUserModel.user_id == 1,
            WordModel.is_active == True,
            GameModel.is_active == True
        )

        games_words_result = [row for row in db.engine.connect().execute(games_words_query)]

        games_words_objects = []
        for row in games_words_result:
            games_words_objects.append(
                {
                    'game': {
                        'game_id': row[1],
                        'game_name': row[2],
                        'developer': row[3]
                    },
                    'word' : {
                        'word_id': row[4],
                        'word': row[5],
                        'definition': row[6],
                        'example': row[7],
                        'submit_datetime': row[8]
                    }
                }
            )

        return jsonify(games_words_objects), 200

# Return (return game and word)