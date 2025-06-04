from flask.views import MethodView
from flask_jwt_extended import get_jwt, jwt_required
from flask_smorest import Blueprint, abort
from json import load as jsonload
from random import randint
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func
from flask import jsonify

from db import db
from models import GameModel, WordModel, GamesWordsModel, UserModel
from schemas import (GameSchema,
                     GameUpdateSchema,
                     WordSchema,
                     SearchSchema,
                     GamesSearchResultSchema,
                     GameWordsSearchResultSchema)

words_per_game = 4
query_limit = 15

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
    @blp.response(200, GamesSearchResultSchema(many=True))
    def get(self, args: dict):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)

        filters = [GameModel.is_active.is_(True)]
        if 'startsWith' in args:
            filters.append(GameModel.game_name.ilike(args['startsWith'] + '%'))
        if 'name' in args:
            filters.append(GameModel.game_name.ilike('%' + args['name'] + '%'))


        first_subquery = select(
                GameModel.game_id,
                GameModel.game_name
            ).where(*filters
            ).offset(query_limit * (page - 1)
            ).limit(query_limit)
        
        second_subquery = select(
                first_subquery.c,
                GamesWordsModel.word_id,
                func.rank().over(partition_by=first_subquery.c.game_id).label('rn')
            ).join(GamesWordsModel)
        
        last_subquery = select(
                second_subquery.c.game_id,
                second_subquery.c.game_name,
                WordModel.word_id,
                WordModel.word
            ).join(WordModel
            ).where(second_subquery.c.rn<=words_per_game)


        query_results = [row for row in db.engine.connect().execute(last_subquery)]
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

        return output_results
    
@blp.route('/games/random')
class GameRandom(MethodView):
    @blp.response(200, GameSchema)
    def get(self):
        game_count = None
        with open('metadata.json', 'r') as metadata:
            game_count = jsonload(metadata)['game_count']
    
        if not game_count:
            game_count = GameModel.query.count()

        inactive_games_found = set()
        while True:
            random_row_number = randint(0, game_count - 1)
            while random_row_number in inactive_games_found:
                random_row_number = randint(0, game_count)
            game = GameModel.query.offset(random_row_number).first()
            if game and game.is_active:
                break
            inactive_games_found.add(random_row_number)
            if len(inactive_games_found) >= game_count:
                abort(404, message='Could not find a game')

        return game

@blp.route('/games/<int:game_id>/words')
class GameWordsList(MethodView):
    @blp.arguments(SearchSchema, location='query')
    @blp.response(200, GameWordsSearchResultSchema)
    def get(self, args:dict, game_id: int):
        return GamesWordsLookup(args, game_id)
    

@blp.route('/games/<int:game_id>/words/search')
class GamesWordsSearch(MethodView):
    @blp.arguments(SearchSchema, location='query')
    @blp.response(200, GameWordsSearchResultSchema)
    def get(self, args: dict, game_id: int):
        if 'word' not in args and 'startsWith' not in args:
            abort(403, message='Must include either \'startsWith\' or \'word\' query parameters')
        return GamesWordsLookup(args, game_id)
    

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


def GamesWordsLookup(args, game_id):
    page = args['page'] if 'page' in args else 1
    page = max(page, 1)
    startsWith = args['startsWith'] if 'startsWith' in args else ''
    search_term = args['word'] if 'word' in args else ''
    game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()

    words_query = select(
            WordModel,
            UserModel.username
        ).join(GamesWordsModel
        ).join(UserModel
        ).where(
            GamesWordsModel.game_id.is_(game_id),
            WordModel.is_active.is_(True),
            WordModel.word.ilike(startsWith + '%'),
            WordModel.word.ilike('%' + search_term + '%')
        ).offset(query_limit * (page - 1)
        ).limit(query_limit)
    
    words_objects = {}
    word_ids = set()

    for row in db.engine.connect().execute(words_query):
        word_ids.add(row[0])
        words_objects[row[0]] = {
            'word_id': row[0],
            'word': row[1],
            'definition': row[2],
            'example': row[3],
            'author_id': row[4],
            'published': row[5],
            'submit_datetime': row[6],
            'is_active': row[7],
            'upvotes': row[8],
            'downvotes': row[9],
            'author_username': row[10],
            'games': []
        }
    
    games_first_query = select(
            GamesWordsModel,
            GameModel.game_name,
            func.rank().over(partition_by=GamesWordsModel.word_id, order_by=GamesWordsModel.game_id).label('rn')
        ).join(GameModel
        ).where(GamesWordsModel.word_id.in_(word_ids)
        )
    
    games_second_query = select(
            games_first_query.c.word_id,
            games_first_query.c.game_id,
            games_first_query.c.game_name
        ).where(games_first_query.c.rn <= 4)
    
    for row in db.engine.connect().execute(games_second_query):
        words_objects[row[0]]['games'].append({'game_id': row[1], 'game_name': row[2]})
    
    output_object = {'game_id': game_id, 'game_name': game.game_name, 'words': []}

    for word_id in words_objects:
        output_object['words'].append(words_objects[word_id])

    return output_object