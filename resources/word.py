from datetime import datetime
from flask.views import MethodView
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from flask import request

from db import db
from models import WordModel, GameModel
from schemas import WordSchema, WordUpdateSchema, GameSchema, SearchSchema

blp = Blueprint('Words', __name__, description='Blueprint for /words endpoints')

query_limit = 15


@blp.route('/words/<int:word_id>')
class Word(MethodView):
    @blp.response(200, WordSchema)
    def get(self, word_id: int):
        word = WordModel.query.filter_by(word_id=word_id, is_active=True).first_or_404()
        games_to_return = []
        for game in word.games:
            if game.is_active:
                games_to_return.append(game)
        word.games = games_to_return
    
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


@blp.route('/words')
class WordAdd(MethodView):
    @blp.response(200, WordSchema(many=True))
    def get(self):
        return WordModel.query.all()
    
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

        try:
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
    @blp.arguments(SearchSchema, location='query')
    @blp.response(200, WordSchema(many=True))
    def get(self, args: dict):
        page = args['page'] if 'page' in args else 1
        page = max(page, 1)

        filters = [WordModel.is_active.is_(True)]
        if 'startsWith' in args:
            filters.append(WordModel.word.ilike(args['startsWith'] + '%'))
        if 'word' in args:
            filters.append(WordModel.word.ilike('%' + args['word'] + '%'))


        words_query = WordModel.query.filter(*filters).limit(query_limit).offset(query_limit * (page - 1)).all()

        if not words_query:
            abort(404, message='No words found.')

        for word in words_query:
            word.games = word.games[:4]
    
        return words_query

# Only Admin deletes the game and when it's done, it's permanent so we can delete the games_words_links
# Can straight delete the words and games_words_links (only word poster can do this since it's fine to include multiples of the same word by different people)
# How to update with Wiki/Image URL if not done on initial post?
# Make games_words links need login and they are the ones who can delete it. Anyone can do it. Admins can also delete it. Maybe add permission_bans to offenders
# Can straight delete the games_words links... BUT WHO CAN DO THIS? And how? And when?
# Need flags for words (and maybe games?)
# Flags need to be only usable by signed in persons
# Need Upvotes/Downvotes for words (and maybe games?)
