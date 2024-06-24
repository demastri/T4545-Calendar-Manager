from google.cloud import storage
import json
from LogDetail import LogDetail
import ConfigData


class BucketIo:
    def __init__(self):
        self.project_id = ConfigData.project_id
        self.bucket_id = ConfigData.bucket_id
        self.file_id = None

    def read_data(self, file_id):
        try:
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.get_bucket(self.bucket_id)
            blob = bucket.blob(file_id)
            json_dict = json.loads(blob.download_as_string(client=None))
        except Exception:
            LogDetail().print_log("Error", "Exception in read_data on bucket: <" + self.bucket_id+"> ")
            json_dict = None

        return json_dict

    def write_data(self, json_dict, file_id):
        try:
            out_string = json.dumps(json_dict)

            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.get_bucket(self.bucket_id)
            blob = bucket.blob(file_id)
            blob.upload_from_string(out_string)

        except Exception:
            LogDetail().print_log("Error", "Exception in write_data on bucket: <" + self.bucket_id+"> ")
