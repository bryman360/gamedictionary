from flask import jsonify
from flask.views import MethodView
from flask_jwt_extended import get_jwt, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import GameModel, WordModel, GamesWordsModel
from schemas import GameSchema, GameUpdateSchema, WordSchema, GamesSearchSchema, WordsSearchSchema, GameSearchResultSchema


blp = Blueprint('Games', __name__, description='Blueprint for /game endpoints')


@blp.route('/games/<int:game_id>')
class Game(MethodView):
    @blp.response(200, GameSchema)
    def get(self, game_id):
        return GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()
    
    # TODO: Put in some kind of restriction/rule of who can modify an existing game's info. Maybe just admins once game created?
    @jwt_required()
    @blp.arguments(GameUpdateSchema)
    @blp.response(201, GameSchema)
    def put(self, request_payload, game_id):
        game = GameModel.query.get(game_id)
        if game:
            game.game_name = request_payload['game_name'] if 'game_name' in request_payload else game.game_name
            game.wiki_url = request_payload['wiki_url'] if 'wiki_url' in request_payload else game.wiki_url
            game.image_url = request_payload['image_url'] if 'image_url' in request_payload else game.image_url
        else:
            game = GameModel(**request_payload)
        game.is_active = True
        try:
            db.session.add(game)
            db.session.commit()
            return game
        except SQLAlchemyError:
            abort(500, message='Unable to post to SQL database.')

    # TODO: Flag game/word links to be deleted as well.
    @jwt_required()
    @blp.response(204)
    def delete(self, game_id: str):
        jwt = get_jwt()
        game = GameModel.query.get_or_404(game_id)
        if not jwt.get('is_admin'):
            abort(403, message='Permission denied. Admin privelege required.')

        game.is_active = False
        try:
            db.session.add(game)
            db.session.commit()
            return {}
        except KeyError:
            abort(404, message=f'Game with ID {game_id} not found.')


@blp.route('/games')
class GameList(MethodView):
    @blp.response(200, GameSchema(many=True))
    def get(self):
        return GameModel.query.all()

    @jwt_required()
    @blp.arguments(GameSchema)
    @blp.response(201, GameSchema)
    def post(self, request_payload):
        game = GameModel(**request_payload)
        game.is_active = True
        try:
            db.session.add(game)
            db.session.commit()
            return game
        except SQLAlchemyError:
            abort(500, message='Unable to post to database.')
    

@blp.route('/games/search')
class GamesSearch(MethodView):
    @blp.arguments(GamesSearchSchema, location='query')
    @blp.response(200, GameSchema(many=True))
    def get(self, args: dict):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)

        filters = []
        if 'startsWith' in args:
            filters.append(GameModel.game_name.ilike(args['startsWith'] + '%'))
        if 'name' in args:
            filters.append(GameModel.game_name.ilike('%' + args['name'] + '%'))


        filters.append(WordModel.games.any(game_id=GameModel.game_id))
        
        top_15_games = GameModel.query.filter(*filters).limit(15).offset((page - 1) * 15).all()
        
        results = []
        for game in top_15_games:
            game_result = {'game_id': game.game_id, 'game_name': game.game_name}
            game_word_results = []
            for word in game.words:
                game_word_results.append({'word_id': word.word_id, 'word': word.word})
                if len(game_word_results) == 3:
                    break
            game_result['words'] = game_word_results
            results.append(game_result)

        return results

@blp.route('/games/<int:game_id>/words')
class GameWordsList(MethodView):
    @blp.response(200, WordSchema(many=True))
    def get(self, game_id: int):
        game = GameModel.query.get_or_404(game_id)
        if not game.is_active:
            abort(404)
        
        if game.words:
            words_ouptut = []
            for word in game.words:
                if word.is_active:
                    words_ouptut.append(word)
                if len(words_ouptut) >= 20:
                    break
            return words_ouptut
        else:
            return []
    

@blp.route('/games/<int:game_id>/words/search')
class GamesWordsSearch(MethodView):
    @blp.arguments(WordsSearchSchema, location='query')
    @blp.response(200, WordSchema(many=True))
    def get(self, game_id: int, args: dict):
        page = args['page'] if 'page' in args else 1
        word = args['word']
        
        return WordModel.query.filter(WordModel.word.ilike('%' + word + '%')).limit(15).offset((page - 1) * 15).all()
    

@blp.route('/games/<int:game_id>/words/<int:word_id>')
class LinkGameToWord(MethodView):
    # TODO: Decide if this is allowable by anyone or any user with token.
    @jwt_required()
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
            abort(500, message='Unable to link game and word in database.')
    
    # TODO: Figure out some kind of rule/permission restriction so not anyone can make these deletes.
    @jwt_required()
    @blp.response(204)
    def delete(self, game_id: int, word_id: int):

        jwt = get_jwt()
        if not jwt.get('is_admin'):
            abort(401, message='Permission denied. Admin privelege required.')

        game = GameModel.query.filter_by(game_id=game_id, is_active=True)
        word = WordModel.query.filter_by(word_id=word_id, is_active=True)

        game.words.remove(word)
        try:
            db.session.add(game)
            db.session.commit()
            return {}
        except SQLAlchemyError:
            abort(500, message='Unable to delete game and word link in database.')
