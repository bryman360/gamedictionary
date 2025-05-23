from flask import jsonify
from flask.views import MethodView
from flask_jwt_extended import get_jwt, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func

from db import db
from models import GameModel, WordModel, GamesWordsModel, UserModel
from schemas import GameSchema, GameUpdateSchema, WordSchema, GamesSearchSchema, WordsSearchSchema, GameSearchResultSchema

per_game = 4
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
    @blp.arguments(GamesSearchSchema, location='query')
    # @blp.response(200, GameSearchResultSchema(many=True))
    def get(self, args: dict):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)

        filters = [GameModel.is_active.is_(True)]
        if 'startsWith' in args:
            filters.append(GameModel.game_name.ilike(args['startsWith'] + '%'))
        if 'name' in args:
            filters.append(GameModel.game_name.ilike('%' + args['name'] + '%'))


        first_query = select(GameModel.game_id, GameModel.game_name).where(*filters).offset(per_page * (page - 1)).limit(per_page)
        second_query = select(first_query.c.game_id, first_query.c.game_name, GamesWordsModel.word_id,
                              func.row_number().over(partition_by=first_query.c.game_id).label('rn')).join(GamesWordsModel)
        # Must be Game_id, Game_name, word_id, word
        last_query = select(second_query.c.game_id, second_query.c.game_name, WordModel.word_id, WordModel.word).join(WordModel).where(second_query.c.rn<=4)


        query_results = [row for row in db.engine.connect().execute(last_query)]
        if not query_results:
            abort(404)

        game_objects = {}
        output_results = []
        for query_row in query_results:
            if query_row[0] not in game_objects:
                game_objects[query_row[0]] = {'game_id': query_row[0], 'game_name': query_row[1], 'words': []}
            game_objects[query_row[0]]['words'].append({'word_id': query_row[2], 'word': query_row[3]})

        for game_object in game_objects:
            output_results.append(game_objects[game_object])

        return output_results, 200

@blp.route('/games/<int:game_id>/words')
class GameWordsList(MethodView):
    @blp.arguments(WordsSearchSchema, location='query')
    def get(self, args:dict, game_id: int):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)
        game = GameModel.query.filter_by(game_id=game_id, is_active=True).first_or_404()

        games_words_query = select(GamesWordsModel.word_id,
                                   WordModel.word,
                                   WordModel.definition,
                                   WordModel.example,
                                   WordModel.submit_datetime,
                                   WordModel.author_id,
                            ).join(WordModel).where(
                                GamesWordsModel.game_id.is_(game_id), WordModel.is_active.is_(True)
                            ).offset(per_page * (page - 1)
                            ).limit(per_page)
        
        games_words_with_authors_query = select(games_words_query.c, UserModel.username).join(UserModel)

        query_results = [row for row in db.engine.connect().execute(games_words_with_authors_query)]
        output_object = {'game_id': game_id, 'game_name': game.game_name, 'words': []}
        for query_row in query_results:
            word_object = {'word_id': query_row[0],
                           'word': query_row[1],
                           'definition': query_row[2],
                           'example': query_row[3],
                           'submit_datetime': query_row[4],
                           'author_id': query_row[5],
                           'author_username': query_row[6]}
            output_object['words'].append(word_object)


        return output_object, 200
    

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
