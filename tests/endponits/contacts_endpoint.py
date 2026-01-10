from tests.data.urls import Urls


class ContactsEndpoint:
    def __init__(self, api_client):
        self.api_client = api_client

    def get_contacts(self):
        response = self.api_client.get(Urls.contacts_url)
        assert response.status_code == 200
        return response.json()

    def create_contact(self, contact):
        response = self.api_client.post(url=Urls.contacts_url, json=contact)
        assert response.status_code == 201
        return response.json()
    def delete_contact(self, contact_id):
        response = self.api_client.delete(Urls.contacts_url + '/' + str(contact_id))
        assert response.status_code == 204