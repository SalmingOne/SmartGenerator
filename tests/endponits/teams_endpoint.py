import pytest
from pydantic import ValidationError

from tests.data.models.team_model import Team, Member, TeamList
from tests.data.urls import Urls


class TeamsEndpoint:
    def __init__(self, api_client):
        self.api_client = api_client


    def create_team(self, team):
        response = self.api_client.post(Urls.teams_url, json=team)
        assert response.status_code == 201, response.text
        return response.json()

    def delete_team(self, team_id):
        response = self.api_client.delete(Urls.teams_url + f'/{team_id}')
        assert response.status_code == 204, response.text

    def get_team(self, team_id):
        response = self.api_client.get(Urls.teams_url + f'/{team_id}')
        assert response.status_code == 200, response.text
        try:
            team = Team(**response.json())
            return team
        except Exception as e:
            pytest.fail(e)

    def get_teams(self):
        response = self.api_client.get(Urls.teams_url + f'/list')
        try:
            teams = TeamList(teams=response.json()['teams'])
            return teams
        except Exception as e:
            pytest.fail(e)

    def update_team(self, json):
        response = self.api_client.put(Urls.teams_url+'/edit', json=json)
        assert response.status_code == 200, response.text
        return response.json()

    def add_member(self, json):
        response = self.api_client.post(Urls.teams_url + '/members', json=json)
        assert response.status_code == 201, response.text
        try:
            member = Member(**response.json())
        except ValidationError as e:
            pytest.fail(e)
        return member

    def remove_member(self, team_id, member_id):
        response = self.api_client.delete(Urls.teams_url + f'/members/{team_id}/{member_id}', )
        assert response.status_code == 204, response.text

    def update_member_role(self, json):
        response = self.api_client.put(Urls.teams_url + '/members/role', json=json)
        assert response.status_code == 200, response.text
        try:
            member = Member(**response.json())
        except ValidationError as e:
            pytest.fail(e)
        return member

    def assign_object(self, json, object_type):
        response = self.api_client.post(f"{Urls.teams_url}/{object_type}s/assign", json=json)
        assert response.status_code == 201, response.text
        return response.json()

    def remove_object_from_member(self, json, object_type):
        response = self.api_client.delete(Urls.teams_url + f'/{object_type}s/', params=json)
        assert response.status_code == 204, response.text
        return response

    def get_tasks(self, team_id):
        response = self.api_client.get(Urls.teams_url + '/tasks', params={'team_id': team_id})
        assert response.status_code == 200, response.text
        return response.json()

    def get_member_task(self, team_id, user_id):
        response = self.api_client.get(Urls.teams_url + f'{team_id}/{user_id}/tasks')
        assert response.status_code == 200, response.text
        return response.json()

    def get_user_teams(self, user_id):
        response = self.api_client.get(Urls.teams_url + f'/user/{user_id}')
        assert response.status_code == 200, response.text
        return response.json()
