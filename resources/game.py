import os

from datetime import datetime
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from requests import post
from sqlalchemy import func
from sqlalchemy.orm import load_only

from db import db
from models import GameModel
from schemas import GameSchema, GameSearchSchema

words_per_game = 4
default_query_limit = 10

blp = Blueprint('Games', __name__, description='Blueprint for /games endpoints')


@blp.route('/games/<string:game_slug>')
class Game(MethodView):
    @blp.response(200, GameSchema)
    def get(self, game_slug: str):
        '''Get a specific game's details from IGDB.'''
        igdb_game = post('https://api.igdb.com/v4/games',
                                **{'headers':
                                    {
                                        'Client-ID': os.getenv('IGDB_CLIENT_ID'),
                                        'Authorization': f'Bearer {os.getenv("IGDB_ACCESS_TOKEN")}'
                                    },
                                'data':
                                    f'where slug="{game_slug}";\n\
                                    fields name,summary,first_release_date,involved_companies,cover.url,slug;'
                                }
                            )

        igdb_game_json = igdb_game.json()
        if 'first_release_date' in igdb_game_json[0]:
            igdb_game_json[0]['first_release_date'] = datetime.fromtimestamp(igdb_game_json[0]['first_release_date'])
        if 'cover' in igdb_game_json[0]:
            igdb_game_json[0]['cover_url'] = igdb_game_json[0]['cover']['url']

        return igdb_game_json[0]
    

@blp.route('/games/search')
class GamesSearch(MethodView):
    @blp.arguments(GameSearchSchema, location='query')
    @blp.response(200, GameSchema(many=True))
    def get(self, args: dict):
        '''Search IGDB by game name. Either by "startsWith" or "name".'''
        offset = args['offset'] if 'offset' in args else 0
        offset = max(offset, 0)
        limit = args['limit'] if 'limit' in args else default_query_limit
        limit = min(max(limit, 1), 20)

        name_filter = ''
        if 'startsWith' in args and 'name' in args:
            name_filter=f'name~*"{args["name"]}"* & name~"{args["startsWith"]}"*'
        elif 'startsWith' in args:
            name_filter=f'name~"{args["startsWith"]}"*'
        elif 'name' in args:
            name_filter=f'name~*"{args["name"]}"*'
        else:
            abort(400, message='Must include \'startsWith\' or \'name\' in query parameters.')
        
        igdb_games = post('https://api.igdb.com/v4/games',
                                **{'headers':
                                    {
                                       'Client-ID': os.getenv('IGDB_CLIENT_ID'),
                                        'Authorization': f'Bearer {os.getenv("IGDB_ACCESS_TOKEN")}'
                                    },
                                'data':
                                    f'where {name_filter} & parent_game=null & game_type.type="Main Game" & version_parent=null;\n\
                                    fields name,summary,first_release_date,involved_companies,cover.url,slug;\
                                    limit {limit};\
                                    offset {offset};'
                                }
                            )

        igdb_games_json = igdb_games.json()
        for i in range(len(igdb_games_json)):
            if 'first_release_date' in igdb_games_json[i]:
                igdb_games_json[i]['first_release_date'] = datetime.fromtimestamp(igdb_games_json[i]['first_release_date'])
            if 'cover' in igdb_games_json[i]:
                igdb_games_json[i]['cover_url'] = igdb_games_json[i]['cover']['url']
        return igdb_games_json, 200

    
@blp.route('/games/random')
class GameRandom(MethodView):
    @blp.response(200, GameSchema)
    def get(self):
        '''Get details from IGDB of a random game that has some definitions in GamerDictionary.'''
        game = GameModel.query.options(load_only('game_id')).offset(
            func.floor(
                func.random() * db.session.query(func.count(1)).select_from(GameModel)
            )
        ).limit(1).first()

        igdb_game = post('https://api.igdb.com/v4/games',
                                **{'headers':
                                    {
                                       'Client-ID': os.getenv('IGDB_CLIENT_ID'),
                                        'Authorization': f'Bearer {os.getenv("IGDB_ACCESS_TOKEN")}'
                                    },
                                'data':
                                    f'where id=({game["game_id"]}) & parent_game=null & game_type.type="Main Game" & version_parent=null;\n\
                                    fields name,summary,first_release_date,involved_companies,cover.url,slug;'
                                }
                            )

        igdb_game_json = igdb_game.json()
        if 'first_release_date' in igdb_game_json[0]:
            igdb_game_json[0]['first_release_date'] = datetime.fromtimestamp(igdb_game_json[0]['first_release_date'])
        if 'cover' in igdb_game_json[0]:
            igdb_game_json[0]['cover_url'] = igdb_game_json[0]['cover']['url']

        return igdb_game_json