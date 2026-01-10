import os

from tests.data.urls import Urls
import mimetypes


class FilesEndpoint:

    def __init__(self, api_client):
        self.api_client = api_client

    def upload_file_to_entity(self, file_path, payload):
        mime_type, _ = mimetypes.guess_type(file_path)

        with open(file_path, 'rb') as f:
            files = {
                'file': (
                    os.path.basename(file_path),  # имя файла
                    f,  # содержимое
                    mime_type  # MIME тип
                )
            }

            response = self.api_client.post(
                url=f'{Urls.files_url}/entity/upload',
                data=payload,
                files=files
            )
        assert response.status_code == 200
        return response.json()


    def upload_file_to_comment(self, file_path, payload):
        mime_type, _ = mimetypes.guess_type(file_path)

        with open(file_path, 'rb') as f:
            files = {
                'file': (
                    os.path.basename(file_path),  # имя файла
                    f,  # содержимое
                    mime_type  # MIME тип
                )
            }

            response = self.api_client.post(
                url=f'{Urls.files_url}/comment/upload',
                data=payload,
                files=files
            )

        assert response.status_code == 200
        return response.json()


    def get_entity_files(self, entity_type, entity_id):
        response = self.api_client.get(f'{Urls.files_url}/entity/files/?entity_type={entity_type}&entity_id={entity_id}')
        assert response.status_code == 200
        return response.json()['files']


    def delete_file(self, file_guid):
        response = self.api_client.delete(f'{Urls.files_url}/delete?file_guid={file_guid}')
        assert response.status_code == 200
        return response.json()

    def restore_file(self, file_guid):
        response = self.api_client.patch(f'{Urls.files_url}/{file_guid}/restore')
        assert response.status_code == 200
        return response.json()

    def download_file(self, file_guid, filename=None, save_dir=None):
        response = self.api_client.get(f'{Urls.files_url}/{file_guid}/download')
        assert response.status_code == 200

        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, filename)

        with open(file_path, 'wb') as f:
            f.write(response.content)

        return file_path


