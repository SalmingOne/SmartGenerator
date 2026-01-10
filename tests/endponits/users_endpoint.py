import os

import pytest

from tests.data.models.team_model import Team
from tests.data.models.user_models import User
from tests.data.urls import Urls


class UsersEndpoint:
    def __init__(self, api_client):
        self.api_client = api_client

    def get_user_info(self):
        response = self.api_client.get(Urls.user_info_url)
        assert response.status_code == 200
        try:
            user = User(**response.json())
            return user
        except Exception as e:
            pytest.fail(e)

    def get_team_by_id(self, id):
        try:
            team_data = next((team for team in self.get_user_info().teams if team['team_id'] == id), None)
            team = Team(**team_data)
            return team
        except Exception as e:
            pytest.fail(e)

    def get_first_team(self):
        try:
            team_data = next((team for team in self.get_user_info().teams), None)
            team = Team(**team_data)
            return team
        except Exception as e:
            pytest.fail(e)

    def get_calendars(self):
        return self.get_user_info().calendar_urls


    def add_calendar(self, url):
        reaponse = self.api_client.post(Urls.users_url + '/calendar_url', json=dict(url=url))
        assert reaponse.status_code == 200, reaponse.text
        return reaponse.json()

    def delete_calendar_by_url(self, url):
        calendar_id = next(cal.get('id') for cal in self.get_calendars() if cal.get('url') == url)
        self.delete_calendar(calendar_id)

    def delete_calendar(self, calendar_id):
        self.api_client.delete(Urls.users_url  + f'/{calendar_id}')