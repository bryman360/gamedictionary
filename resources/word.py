from datetime import datetime
from flask.views import MethodView
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_smorest import Blueprint, abort
from json import load as jsonload
from random import randint, shuffle
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import WordModel, UserModel, GameModel
from schemas import WordSchema, WordUpdateSchema, WordSearchSchema, VoteActionSchema, VoteReturnSchema, WordWithUsernameSchema

blp = Blueprint('Words', __name__, description='Blueprint for /words endpoints')

games_per_word = 4
default_query_limit = 10


@blp.route('/words/<int:word_id>')
class Word(MethodView):
    @blp.response(200, WordSchema)
    def get(self, word_id: int):
        word = WordModel.query.filter_by(word_id=word_id, is_active=True).first_or_404()
        return word

    @jwt_required()
    @blp.arguments(WordUpdateSchema)
    @blp.response(200, WordSchema)
    def put(self, request_payload: dict, word_id: int):

        word = WordModel.query.get(word_id)
        jwt = get_jwt()
        current_user = get_jwt_identity()
        if not jwt.get('is_admin') and not current_user == str(word.author_id):
            abort(403, message='Permission denied. User does not have permission to alter word.')
        if word:
            word.word = request_payload['word'] if 'word' in request_payload else word.word
            word.definition = request_payload['definition'] if 'definition' in request_payload else word.definition
            word.example = request_payload['example'] if 'example' in request_payload else word.example
            word.game_id = request_payload['game_id'] if 'game_id' in request_payload else word.game_id
        else:
            word = WordModel(**request_payload)
            word.submit_datetime = datetime.now()
            word.published = False
            word.upvotes = 0
            word.downvotes = 0
        word.is_active = True

        try:
            db.session.add(word)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message='Could not save word to database.')

    @jwt_required()
    @blp.response(204)
    def delete(self, word_id: int):
        jwt = get_jwt()
        current_user = get_jwt_identity()
        word = WordModel.query.get_or_404(word_id)
        if not jwt.get('is_admin') and not current_user == str(word.author_id):
            abort(403, message='Permission denied. User does not have permission to alter word.')
        
        word.is_active = False
        try:
            db.session.add(word)
            db.session.commit()
            return {}
        except SQLAlchemyError:
            abort(500, message=f'Word with ID {word_id} could not be deleted from database.')

@blp.route('/words/vote')
class WordVotes(MethodView):
    @blp.arguments(VoteActionSchema)
    @blp.response(201, VoteReturnSchema)
    def post(self, request_payload: dict):
        word = WordModel.query.filter_by(word_id=request_payload['word_id'], is_active=True).first_or_404()
        if 'upvote_action' in request_payload and \
            'downvote_action' in request_payload and \
            request_payload['upvote_action'] == request_payload['downvote_action']:
                abort(400, message='Cannot have the same action for both upvote and downvote.')
        if 'upvote_action' in request_payload:
            if request_payload['upvote_action'] != 'increment' and request_payload['upvote_action'] != 'decrement':
                abort(400, message="Bad payload. Upvote action needs to be either increment or decrement.")
            elif request_payload['upvote_action'] == 'increment':
                word.upvotes += 1
            elif request_payload['upvote_action'] == 'decrement' and word.upvotes > 0:
                word.upvotes -= 1
        if 'downvote_action' in request_payload:
            if request_payload['downvote_action'] != 'increment' and request_payload['downvote_action'] != 'decrement':
                abort(400, message="Bad payload. Downvote action needs to be either increment or decrement.")
            elif request_payload['downvote_action'] == 'increment':
                word.downvotes += 1
            elif request_payload['downvote_action'] == 'decrement' and word.downvotes > 0:
                word.downvotes -= 1
        try:
            db.session.add(word)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message=f'Word with ID {word.word_id} could not update the votes.')
        
        return word


@blp.route('/words')
class WordAdd(MethodView):
    @blp.response(200, WordSchema(many=True))
    def get(self):
        return WordModel.query.limit(10).all()
    
    @jwt_required()
    @blp.arguments(WordSchema)
    @blp.response(201, WordSchema)
    def post(self, request_payload: dict):
        current_user = get_jwt_identity()
        word = WordModel(**request_payload)
        word.submit_datetime = datetime.now()
        word.published = False
        word.author_id = int(current_user)
        word.is_active = True
        word.upvotes = 0
        word.downvotes = 0

        game = GameModel.query(game_id=request_payload['game_id']).first()
        new_game = None
        if not game:
            new_game = GameModel({'game_id': request_payload['game_id']})
        # new_game.words.append(word)

        try:
            if new_game:
                db.session.add(new_game)
            db.session.add(word)
            db.session.commit()
            return word
        except SQLAlchemyError:
            abort(500, message='Unable to save word to database.')
            

# @blp.route('/word/<int:word_id>/flag')
# class Word(MethodView):
#     @jwt_required()
#     @blp.arguments(WordUpdateSchema)
#     @blp.response(200, WordSchema)
#     def post(self, request_payload: dict, word_id: int):

#         word = WordModel.query.get_or_404(word_id)
#         # word.flag_count = word.flag_count + 1

#         try:
#             db.session.add(word)
#             db.session.commit()
#             return word
#         except SQLAlchemyError:
#             abort(500, message='Could not save word to database.')
    

@blp.route('/words/search')
class WordSearch(MethodView):
    @blp.arguments(WordSearchSchema, location='query')
    @blp.response(200, WordWithUsernameSchema(many=True))
    def get(self, args: dict):
        offset = args['offset'] if 'offset' in args else 0
        offset = max(offset, 0)
        limit = args['limit'] if 'limit' in args else default_query_limit
        limit = max(limit, 1)

        filters = [WordModel.is_active.is_(True)]
        if 'startsWith' in args and 'word' in args:
            abort(400, message='Must include \'startsWith\' OR \'word\' in query parameters, not both.')
        elif 'startsWith' in args:
            if (args['startsWith'] == '*'):
                regex_pattern = r'^[^A-Za-z].*'
                filters.append(WordModel.word.op('regexp')(regex_pattern))
            else:
                filters.append(WordModel.word.ilike(args['startsWith'] + '%'))
        elif 'word' in args:
            filters.append(WordModel.word.ilike('%' + args['word'] + '%'))
        if 'author' in args:
            filters.append(WordModel.user.has(username=args['author']))
        if 'game_id' in args:
            filters.append(WordModel.game_id.is_(args['game_id']))

        words_query = select(
                WordModel,
                UserModel.username
            ).join(UserModel
            ).where(*filters
            ).offset(offset
            ).limit(limit)

        words_query_result = [row for row in db.engine.connect().execute(words_query)]
        return words_query_result
    
@blp.route('/words/random')
class RandomWords(MethodView):
    @blp.response(200, WordWithUsernameSchema(many=True))
    def get(self):
        word_count = None
        with open('metadata.json', 'r') as metadata:
            word_count = jsonload(metadata)['word_count']
        if not word_count:
            word_count = WordModel.query.count()
        
        limit_amount = min(30, word_count)
        
        last_acceptable_offset_amount = word_count - limit_amount

        start_loc = randint(0, last_acceptable_offset_amount)

        random_section_of_words_query = select(
                WordModel,
                UserModel.username
            ).join(UserModel
            ).offset(start_loc
            ).limit(limit_amount)

        randomized_selection_order = [i for i in range(limit_amount)]
        shuffle(randomized_selection_order)
        words_objects = []


        random_words_query_result = [row for row in db.engine.connect().execute(random_section_of_words_query)]
        if len(random_words_query_result) == 0:
            return []
        

        for i in randomized_selection_order:
            is_active = random_words_query_result[i][7]
            if not is_active:
                continue
            words_objects.append({
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
                'game_id': random_words_query_result[i][10],
                'author_username': random_words_query_result[i][11],
            })
            if len(words_objects) == 7:
                break
        
        return words_objects

@blp.route('/words/mywords')
class MyWords(MethodView):
    @jwt_required()
    @blp.response(200, WordSchema(many=True))
    def get(self):
        user_id = get_jwt_identity()
        words = WordModel.query.filter_by(is_active=True, author_id=user_id).all()
        return words
