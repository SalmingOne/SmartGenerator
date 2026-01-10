import json

from tests.data.urls import Urls


class CommentsEndpoint:
    def __init__(self, api_client):
        self.api_client = api_client

    def create_comment(self, comment):
        response = self.api_client.post(url=Urls.comments_url, json=comment)
        assert response.status_code == 200
        return response.json()

    def delete_comment(self, comment_id):
        response = self.api_client.delete(url=f'{Urls.comments_url}/{comment_id}')
        assert response.status_code == 200
        return response.json()

    def update_comment(self, comment_id, comment):
        response = self.api_client.put(url=f'{Urls.comments_url}/{comment_id}', json=comment)
        assert response.status_code == 200
        return response.json()

    def stream_comments(self, entity_type, entity_id):
        response = self.api_client.get(url=f'{Urls.streams_url}/comments?entity_type={entity_type}&entity_id={entity_id}', stream=True)
        assert response.status_code == 200

        for line in response.iter_lines():
            line_str = line.decode('utf-8')
            if 'data: b' in line_str:
                start_idx = line_str.find('b\'') + 2
                end_idx = line_str.rfind('\'')

                if start_idx < end_idx:
                    json_str = line_str[start_idx:end_idx]
                    try:
                        yield json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
        return None
