from tests.data.urls import Urls


class MainEndpoint:

    def __init__(self, api_client):
        self.api_client = api_client

    def get_all_by_date(self, date):
        response = self.api_client.get(url=f'{Urls.main_url}/date', params={'date':date})
        assert response.status_code == 200
        return response.json()['all']
