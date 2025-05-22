import json
import os
import requests

from datetime import datetime
from dotenv import load_dotenv

load_dotenv('../.env')
BASE_URL = os.getenv('BASE_URL')

def signin(username, password):
    header = {'Content-Type': 'application/json'}
    body = json.dumps({'username': username, 'password': password})
    signin_response = requests.post(BASE_URL + '/login', headers=header, data=body)

    signin_data = signin_response.json()
    assert signin_response.status_code == 200
    assert isinstance(signin_data, dict)
    assert 'access_token' in signin_data
    assert 'refresh_token' in signin_data

    access_token = signin_data['access_token']
    refresh_token = signin_data['refresh_token']
    signed_in = True
    return access_token, refresh_token, signed_in