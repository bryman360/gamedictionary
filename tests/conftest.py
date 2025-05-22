import json
import os
import pytest
import requests

from dotenv import load_dotenv

@pytest.fixture
def login_credentials():
    load_dotenv('../.env')
    BASE_URL = os.getenv('BASE_URL')
    username = os.getenv('TEST_USERNAME')
    password = os.getenv('TEST_PASSWORD')

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
    credentials = {"access_token": access_token, "refresh_token": refresh_token, "signed_in": signed_in}
    return credentials