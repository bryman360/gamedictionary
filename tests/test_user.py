import json
import jwt
import os
import pytest
import random
import requests

from datetime import datetime
from dotenv import load_dotenv
from math import floor
from tests.utils import signin

load_dotenv('../.env')
BASE_URL = os.getenv('BASE_URL')

username = os.getenv('TEST_USER_USERNAME')
password = os.getenv('TEST_USER_PASSWORD')
jwt_secret = os.getenv('JWT_SECRET_KEY')


def test_user_login():
    header = {'Content-Type': 'application/json'}
    body = json.dumps({'username': 'INVALID_USER', 'password': 'INVALID_PASSWORD'})

    failed_login_response = requests.post(BASE_URL + '/login', headers=header, data=body)

    assert failed_login_response.status_code == 401

    signin(username, password)


def test_user_logout():
    access_token, refresh_token, signed_in = signin(username, password)
    jwt_token = jwt.decode(access_token, jwt_secret, algorithms='HS256')
    user_id = jwt_token['sub']

    header = {'Authorization': 'Bearer ' + access_token}
    requests.post(BASE_URL + '/logout', headers=header)
    
    header['Content-Type'] = 'application/json'
    body = json.dumps({
        'word': 'Failed Word',
        'definition': 'A word that shouldn\'t be posted',
        'example': 'A failed word should not be saved to the DB.'
    })
    word_post_response = requests.post(BASE_URL + '/word', headers=header, data=body)
    word_post_data = word_post_response.json()
    assert word_post_response.status_code == 200
    assert 'error' in word_post_data
    assert word_post_data['error'] == 'token_revoked'
    

def test_user_signup_and_delete():
    char_list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    char_list_len = len(char_list)
    new_username_len = random.randint(6, 10)

    new_username = ''
    for i in range(new_username_len):
        new_username += char_list[random.randint(0, char_list_len - 1)]

    new_password_len = random.randint(6, 10)
    
    new_password = ''
    for i in range(new_password_len):
        new_password += char_list[random.randint(0, char_list_len - 1)]
    
    header = {'Content-Type': 'application/json'}
    body = json.dumps({'username': new_username, 'password': new_password})
    successful_register_response = requests.post(BASE_URL + '/register', headers=header, data=body)

    successful_register_data = successful_register_response.json()
    assert successful_register_response.status_code == 201
    assert isinstance(successful_register_data, dict)
    assert 'access_token' in successful_register_data
    assert 'refresh_token' in successful_register_data

    duplicate_register_response = requests.post(BASE_URL + '/register', headers=header, data=body)
    assert duplicate_register_response.status_code == 409


    jwt_token = jwt.decode(successful_register_data['access_token'], jwt_secret, algorithms='HS256')
    user_id = jwt_token['sub']
    header['Authorization'] = 'Bearer ' + successful_register_data['access_token']

    delete_response = requests.delete(BASE_URL + '/user/' + str(user_id), headers=header)
    assert delete_response.status_code == 204

# TODO: test_user_refresh(), test_user_update()