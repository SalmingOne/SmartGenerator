from tests.data.urls import Urls


class ReactionsEndpoint:

    def __init__(self, api_client):
        self.api_client = api_client

    def add_reaction(self, payload):
        response = self.api_client.post(Urls.reactions_url, data=payload)
        assert response.status_code == 200
        return response.json()

    def get_reactions(self, entity_type, entity_id):
        response = self.api_client.get(url=f'{Urls.reactions_url}?entity_type={entity_type}&entity_id={entity_id}')
        assert response.status_code == 200
        return response.json()['reactions']