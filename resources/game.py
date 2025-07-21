from flask.views import MethodView
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from flask_smorest import Blueprint, abort
from json import load as jsonload
from random import randint, shuffle
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func

from db import db
from models import GameModel, WordModel, GamesWordsModel, UserModel, GamesWordsLinkUserModel
from schemas import (GameSchema,
                     GameUpdateSchema,
                     WordSchema,
                     SearchSchema,
                     GamesSearchResultSchema,
                     GameWordsSearchResultSchema)

words_per_game = 4
default_query_limit = 10

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
            game.developer = request_payload['developer'] if 'developer' in request_payload else game.developer
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
        if 'developer' in request_payload:
            existing_game = GameModel.query.filter_by(game_name=request_payload['game_name'], developer=request_payload['developer']).first()
        else:
            existing_game = GameModel.query.filter_by(game_name=request_payload['game_name']).first()
        if existing_game:
            abort(409, message='Game arleady exists.')
        
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
        offset = args['offset'] if 'offset' in args else 0
        offset = max(offset, 0)
        limit = args['limit'] if 'limit' in args else default_query_limit
        limit = max(limit, 1)

        filters = [GameModel.is_active.is_(True)]
        if 'startsWith' in args:
            if args['startsWith'] == '*':
                regex_pattern = r'^[^A-Za-z].*'
                filters.append(GameModel.game_name.op('regexp')(regex_pattern))
            else:
                filters.append(GameModel.game_name.ilike(args['startsWith'] + '%'))
        if 'name' in args:
            filters.append(GameModel.game_name.ilike('%' + args['name'] + '%'))

        games_query = select(
                GameModel.game_id,
                GameModel.game_name,
                GameModel.developer
            ).where(*filters
            ).offset(offset
            ).limit(limit)
        
        games_query_result = [row for row in db.engine.connect().execute(games_query)]

        if not games_query_result:
            abort(404)

        game_ids = []
        game_objects = {}
        for query_row in games_query_result:
            game_id = query_row[0]
            game_name = query_row[1]
            developer = query_row[2]
            game_ids.append(query_row[0])
            game_objects[query_row[0]] = {'game_id': game_id,
                                          'game_name': game_name,
                                          'developer': developer,
                                          'words': []}

        games_words_query = select(
                GamesWordsModel,
                func.rank().over(partition_by=GamesWordsModel.game_id, order_by=GamesWordsModel.word_id).label('rn')
            ).where(GamesWordsModel.game_id.in_(game_ids))
        
        words_query = select(
                games_words_query.c.game_id,
                WordModel.word_id,
                WordModel.word
            ).join(WordModel
            ).where(games_words_query.c.rn<=words_per_game)


        words_query_result = [row for row in db.engine.connect().execute(words_query)]

        output_results = []
        for query_row in words_query_result:
            game_id = query_row[0]
            word_id = query_row[1]
            word = query_row[2]
            game_objects[game_id]['words'].append({'word_id': word_id, 'word': word})

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

        random_row_number = -1
        inactive_games_found = set([random_row_number])
        while True:
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
    

@blp.route('/games/<int:game_id>/words/random')
class GameWordsList(MethodView):
    @blp.response(200, GameWordsSearchResultSchema)
    def get(self, game_id: int):
        game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()

        word_count = GamesWordsModel.query.filter_by(game_id=game_id).count()

        if not word_count or word_count == 0:
            abort(404, message='No words found for game: ' + game.game_name) 

        limit_amount = min(30, word_count)
        last_acceptable_offset_amount = word_count - limit_amount
        start_loc = randint(0, last_acceptable_offset_amount)

        random_section_of_words_query = select(
                WordModel,
                UserModel.username
            ).join(GamesWordsModel
            ).join(UserModel
            ).where(GamesWordsModel.game_id.is_(game_id), WordModel.is_active.is_(True)
            ).offset(start_loc
            ).limit(limit_amount)
        

        randomized_selection_order = [i for i in range(limit_amount)]
        shuffle(randomized_selection_order)
        word_ids = set()
        words_objects = {}

        random_words_query_result = [row for row in db.engine.connect().execute(random_section_of_words_query)]

        for i in randomized_selection_order:
            word_ids.add(random_words_query_result[i][0])
            words_objects[random_words_query_result[i][0]] = {
                'word_id': random_words_query_result[i][0],
                'word': random_words_query_result[i][1],
                'definition': random_words_query_result[i][2],
                'example': random_words_query_result[i][3],
                'author_id': random_words_query_result[i][4],
                'published': random_words_query_result[i][5],
                'submit_datetime': random_words_query_result[i][6],
                'is_active': random_words_query_result[i][7],
                'upvotes': random_words_query_result[i][8],
                'downvotes': random_words_query_result[i][9],
                'author_username': random_words_query_result[i][10],
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
    

@blp.route('/games/<int:game_id>/words/search')
class GamesWordsSearch(MethodView):
    @blp.arguments(SearchSchema, location='query')
    @blp.response(200, GameWordsSearchResultSchema)
    def get(self, args: dict, game_id: int):
        if 'word' not in args and 'startsWith' not in args:
            abort(403, message='Must include either \'startsWith\' or \'word\' query parameters')
        return GamesWordsLookup(args, game_id)
    

def GamesWordsLookup(args, game_id):
    game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()

    offset = args['offset'] if 'offset' in args else 0
    offset = max(offset, 0)
    limit = args['limit'] if 'limit' in args else default_query_limit
    limit = max(limit, 1)

    filters = [WordModel.is_active.is_(True), GamesWordsModel.game_id.is_(game_id)]
    if 'startsWith' in args:
        filters.append(WordModel.word.ilike(args['startsWith'] + '%'))
    if 'word' in args:
        filters.append(WordModel.word.ilike('%' + args['word'] + '%'))

    words_query = select(
            WordModel,
            UserModel.username
        ).join(GamesWordsModel
        ).join(UserModel
        ).where(*filters
        ).offset(offset
        ).limit(limit)
    
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
    
    output_object = {'game_id': game_id, 'game_name': game.game_name, 'developer': game.developer, 'words': []}

    for word_id in words_objects:
        output_object['words'].append(words_objects[word_id])

    return output_object