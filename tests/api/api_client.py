import os

import requests
from dotenv import load_dotenv

from tests.data.urls import Urls

load_dotenv()


def authenticate(session):
    url = f'{Urls.base_url}/auth/login'
    payload = {
            "init_data": f"{os.getenv('QUERY_ID')}",
            "timezone": "Europe/Moscow"
        }
    r = session.post(url, json=payload, verify=False, allow_redirects=False)
    print(r)
    return r.json()['access_token']