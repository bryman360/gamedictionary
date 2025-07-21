from flask import abort
from flask.views import MethodView
from flask_smorest import Blueprint
from json import load as jsonload

blp = Blueprint('Utils', __name__, 'Blueprint for Utility functions.')

@blp.route('/stats')
class Stats(MethodView):
    def get(self):
        game_count = None
        word_count = None
        with open('metadata.json', 'r') as metadata:
            loaded_data = jsonload(metadata)
            game_count = loaded_data['game_count']
            word_count = loaded_data['word_count']
        if not game_count or not word_count:
            abort(400)
        
        return {'game_count': game_count, 'word_count': word_count}, 200
