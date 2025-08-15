from flask import abort
from flask.views import MethodView
from flask_smorest import Blueprint
from json import load as jsonload
from models import WordModel, GameModel, UserModel

blp = Blueprint('Utils', __name__, 'Blueprint for Utility functions.')

@blp.route('/stats')
class Stats(MethodView):
    def get(self):
        word_count = WordModel.query.count()
        game_count = GameModel.query.count()
        user_count = UserModel.query.count()
        
        return {'game_count': game_count, 'word_count': word_count, 'user_count': user_count}, 200

@blp.route('/')
class Health(MethodView):
    def get(self):
        return {}, 200