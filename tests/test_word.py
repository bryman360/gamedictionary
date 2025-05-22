import json
import jwt
import os
import pytest
import random
import requests

from datetime import datetime
from dotenv import load_dotenv
from tests.utils import signin

load_dotenv('../.env')
BASE_URL = os.getenv('BASE_URL')

username = os.getenv('TEST_USER_USERNAME')
password = os.getenv('TEST_USER_PASSWORD')
jwt_secret = os.getenv('JWT_SECRET_KEY')


def test_word_lookup():
    lookup_response = requests.get(BASE_URL + '/word/1')

    lookup_data = lookup_response.json()
    assert lookup_response.status_code == 200
    assert isinstance(lookup_data, dict)
    assert 'word' in lookup_data
    assert 'definition' in lookup_data
    assert 'example' in lookup_data

def test_word_post_modification_and_delete():
    access_token, refresh_token, signed_in = signin(username, password)
    word_str = 'TEST_WORD'
    def_str = 'Just for testing purposes'
    ex_str = 'This is a TEST_WORD'
    header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + access_token}
    word_post_body = json.dumps({'word': word_str, 'definition': def_str, 'example': ex_str})

    word_post_response = requests.post(BASE_URL + '/word', headers=header, data=word_post_body)

    word_post_data = word_post_response.json()
    assert word_post_response.status_code == 201
    assert 'word_id' in word_post_data
    assert isinstance(word_post_data, dict)
    assert 'word' in word_post_data
    assert 'definition' in word_post_data
    assert 'example' in word_post_data
    assert 'author_id' in word_post_data
    assert 'published' in word_post_data
    assert 'submit_datetime' in word_post_data
    assert 'games' in word_post_data

    assert word_post_data['definition'] == def_str
    assert word_post_data['word'] == word_str
    assert word_post_data['example'] == ex_str
    assert word_post_data['published'] == False
    assert len(word_post_data['games']) == 0

    word_id = word_post_data['word_id']

    word_str_modified = 'TEST_WORD_2'
    ex_str_modified = 'This is a TEST_WORD_2'

    word_put_body = json.dumps({'word': word_str_modified, 'definition': def_str, 'example': ex_str_modified})

    word_put_response = requests.put(BASE_URL + '/word/' + word_id, headers=header, data=word_put_body)

    word_put_data = word_put_response.json()
    assert word_put_response.status_code == 200
    assert isinstance(word_put_data, dict)
    assert 'word_id' in word_put_data
    assert 'word' in word_put_data
    assert 'definition' in word_put_data
    assert 'example' in word_put_data
    assert 'author_id' in word_put_data
    assert 'published' in word_put_data
    assert 'submit_datetime' in word_put_data
    assert 'games' in word_put_data

    assert word_put_data['word_id'] == word_post_data['word_id']
    assert word_put_data['word'] == word_str_modified
    assert word_put_data['definition'] == def_str
    assert word_put_data['example'] == ex_str_modified
    assert word_put_data['author_id'] == word_post_data['author_id']
    assert word_put_data['published'] == False
    assert word_put_data['submit_datetime'] == word_post_data['submit_datetime']
    assert len(word_put_data['games']) == 0

    delete_response = requests.delete(BASE_URL + '/word/' + word_id, headers=header)

    assert delete_response.status_code == 204
    
    lookup_response = requests.get(BASE_URL + '/word/' + word_id)

    assert lookup_response.status_code == 404
