from google.cloud import storage
import json

from LogDetail import LogDetail


class Bucket_IO:
    def __init__(self, project_id, bucket_id, blob_id):
        self.project_id = project_id
        self.bucket_id = bucket_id
        self.blob_id = blob_id

    def read_data(self):
        try:
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.get_bucket(self.bucket_id)
            blob = bucket.blob(self.blob_id)
            json_dict = json.loads(blob.download_as_string(client=None))
        except Exception as e:
            LogDetail().print_log("Error", "Exception in read_data on bucket: <" + self.bucket_id+"> ")

        return json_dict

    def write_data(self, json_dict):
        try:
            outString = json.dumps(json_dict)

            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.get_bucket(self.bucket_id)
            blob = bucket.blob(self.blob_id)
            blob.upload_from_string(outString)
        except Exception as e:
            LogDetail().print_log("Error", "Exception in write_data on bucket: <" + self.bucket_id+"> ")
