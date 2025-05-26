from flask import jsonify
from flask.views import MethodView
from flask_jwt_extended import get_jwt, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func
from datetime import datetime

from db import db
from models import GameModel, WordModel, GamesWordsModel, UserModel
from schemas import (GameSchema,
                     GameUpdateSchema,
                     WordSchema,
                     SearchSchema,
                     GameWordsSearchResultSchema)

words_per_game = 4
per_page = 15

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
        game = GameModel.query.filter_by(game_id=game_id, is_active=True).first()
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
        return GameModel.query.filter_by(is_active=True).all()

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
    @blp.arguments(SearchSchema, location='query')
    # @blp.response(200, GameSearchResultSchema(many=True))
    def get(self, args: dict):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)

        filters = [GameModel.is_active.is_(True)]
        if 'startsWith' in args:
            filters.append(GameModel.game_name.ilike(args['startsWith'] + '%'))
        if 'name' in args:
            filters.append(GameModel.game_name.ilike('%' + args['name'] + '%'))


        first_query = select(
                GameModel.game_id,
                GameModel.game_name
            ).where(*filters
            ).offset(per_page * (page - 1)
            ).limit(per_page)
        
        second_query = select(
                first_query.c,
                GamesWordsModel.word_id,
                func.row_number().over(partition_by=first_query.c.game_id).label('rn')
            ).join(GamesWordsModel)
        
        last_query = select(
                second_query.c.game_id,
                second_query.c.game_name,
                WordModel.word_id,
                WordModel.word
            ).join(WordModel
            ).where(second_query.c.rn<=words_per_game)


        query_results = [row for row in db.engine.connect().execute(last_query)]
        if not query_results:
            abort(404)

        game_objects = {}
        output_results = []
        for query_row in query_results:
            row_game_id = query_row[0]
            row_game_name = query_row[1]
            row_word_id = query_row[2]
            row_word = query_row[3]
            if row_game_id not in game_objects:
                game_objects[row_game_id] = {'game_id': row_game_id,
                                             'game_name': row_game_name,
                                             'words': []}
            game_objects[row_game_id]['words'].append({'word_id': row_word_id, 'word': row_word})

        for game_id in game_objects:
            output_results.append(game_objects[game_id])

        return output_results, 200

@blp.route('/games/<int:game_id>/words')
class GameWordsList(MethodView):
    @blp.arguments(SearchSchema, location='query')
    @blp.response(200, GameWordsSearchResultSchema(exclude=['is_active']))
    def get(self, args:dict, game_id: int):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)
        game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()

        games_words_query = select(
                WordModel
            ).join(GamesWordsModel
            ).where(
                GamesWordsModel.game_id.is_(game_id),
                WordModel.is_active.is_(True)
            ).offset(per_page * (page - 1)
            ).limit(per_page)
        
        games_words_with_authors_query = select(
                games_words_query.c,
                UserModel.username
            ).join(UserModel)

        query_results = [row for row in db.engine.connect().execute(games_words_with_authors_query)]
        output_object = {'game_id': game_id, 'game_name': game.game_name, 'words': []}

        for query_row in query_results:
            row_word_id = query_row[0]
            row_word = query_row[1]
            row_definition = query_row[2]
            row_example = query_row[3]
            row_author_id = query_row[4]
            row_submit_datetime = query_row[6]
            row_author_username = query_row[-1]

            word_object = {'word_id': row_word_id,
                           'word': row_word,
                           'definition': row_definition,
                           'example': row_example,
                           'submit_datetime': row_submit_datetime,
                           'author_id': row_author_id,
                           'author_username': row_author_username}

            output_object['words'].append(word_object)

        return output_object
    

@blp.route('/games/<int:game_id>/words/search')
class GamesWordsSearch(MethodView):
    @blp.arguments(SearchSchema, location='query')
    @blp.response(200, GameWordsSearchResultSchema)
    def get(self, args: dict, game_id: int):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)
        game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404('Game not found')

        filters = [WordModel.is_active.is_(True), GamesWordsModel.game_id.is_(game_id)]
        if 'startsWith' in args:
            filters.append(WordModel.word.ilike(args['startsWith'] + '%'))
        if 'word' in args:
            filters.append(WordModel.word.ilike('%' + args['word'] + '%'))


        games_words_query = select(
                WordModel
            ).join(GamesWordsModel
            ).where(*filters
            ).offset(per_page * (page - 1)
            ).limit(per_page)
        
        words_with_author_username_query = select(
                games_words_query.c,
                UserModel.username
            ).join(UserModel)

        query_results = [row for row in db.engine.connect().execute(words_with_author_username_query)]
        
        output_object = {'game_id': game_id, 'game_name': game.game_name, 'words': []}

        for query_row in query_results:
            row_word_id = query_row[0]
            row_word = query_row[1]
            row_definition = query_row[2]
            row_example = query_row[3]
            row_author_id = query_row[4]
            row_submit_datetime = query_row[6]
            row_author_username = query_row[-1]
            print(query_row)
            word_object = {'word_id': row_word_id,
                           'word': row_word,
                           'definition': row_definition,
                           'example': row_example,
                           'submit_datetime': row_submit_datetime,
                           'author_id': row_author_id,
                           'author_username': row_author_username}

            output_object['words'].append(word_object)
        

        return output_object
    

@blp.route('/games/<int:game_id>/words/<int:word_id>')
class LinkGameToWord(MethodView):
    # TODO: Decide if this is allowable by anyone or any user with token.
    @jwt_required()
    @blp.response(201, WordSchema)
    def post(self, game_id: int, word_id: int):
        game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()
        print(game)
        word = WordModel.query.filter_by(word_id=word_id, is_active=True).first_or_404()
        print(word)
        
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
