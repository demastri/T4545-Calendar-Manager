from google.cloud import storage
import json


class Bucket_IO:
    def __init__(self, project_id, bucket_id, blob_id):
        self.project_id = project_id
        self.bucket_id = bucket_id
        self.blob_id = blob_id

    def read_data(self):
        storage_client = storage.Client(project=self.project_id)
        bucket = storage_client.get_bucket(self.bucket_id)
        blob = bucket.blob(self.blob_id)
        json_dict = json.loads(blob.download_as_string(client=None))

        return json_dict

    def write_data(self, json_dict):
        outString = json.dumps(json_dict)

        storage_client = storage.Client(project=self.project_id)
        bucket = storage_client.get_bucket(self.bucket_id)
        blob = bucket.blob(self.blob_id)
        blob.upload_from_string(outString)
