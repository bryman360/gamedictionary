import json
import jwt
import os
import pytest
import random
import requests

print("HI")

from datetime import datetime
from dotenv import load_dotenv
from tests.utils import signin

load_dotenv('../.env')
BASE_URL = os.getenv('BASE_URL')

username = os.getenv('TEST_USER_USERNAME')
password = os.getenv('TEST_USER_PASSWORD')
jwt_secret = os.getenv('JWT_SECRET_KEY')

def test_game_lookup():
    game_lookup_response = requests.get(BASE_URL + '/game/1')

    game_lookup_data = game_lookup_response.json()
    assert game_lookup_response.status_code == 200
    assert isinstance(game_lookup_data, dict)
    assert 'game_id' in game_lookup_data
    assert 'game_name' in game_lookup_data
    assert 'words' in game_lookup_data

def test_word_post_modification_and_delete():
    access_token, refresh_token, signed_in = signin(username, password)
    game_name_str = 'TEST_GAME'
    header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + access_token}
    game_post_body = json.dumps({'game_name': game_name_str})

    game_post_response = requests.post(BASE_URL + '/game', headers=header, data=game_post_body)

    game_post_data = game_post_response.json()
    assert game_post_response.status_code == 201
    assert isinstance(game_post_data, dict)
    assert 'game_name' in game_post_data
    assert 'words' in game_post_data

    assert game_post_data['game_name'] == game_name_str
    assert len(game_post_data['words']) == 0

    game_id = game_post_data['game_id']

    game_name_str_modified = 'TEST_GAME_2'

    game_put_body = json.dumps({'game_name': game_name_str_modified})

    game_put_response = requests.put(BASE_URL + '/game/' + game_id, headers=header, data=game_put_body)

    game_put_data = game_put_response.json()
    assert game_put_response.status_code == 201
    assert isinstance(game_put_data, dict)
    assert 'game_name' in game_put_data
    assert 'words' in game_put_data

    assert game_put_data['game_name'] == game_name_str_modified
    assert len(game_put_data['words']) == 0

    delete_response = requests.delete(BASE_URL + '/game/' + game_id, headers=header)

    assert delete_response.status_code == 204
    
    game_lookup_response = requests.get(BASE_URL + '/game/' + game_id)

    assert game_lookup_response.status_code == 404
