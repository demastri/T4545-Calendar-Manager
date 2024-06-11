from Bucket_IO import Bucket_IO


class ConfigData(object):

    local_config = None

    def __init__(self):
        local_dict = (Bucket_IO(
            ConfigData.project_id(), ConfigData.local_bucket_id(), ConfigData.local_config_blob())
                .read_data())
        self.credential_file = local_dict['credential-file']
        self.data_file = local_dict['data-file']
        self.days_to_keep_events = local_dict['days-to-keep-events']
        self.games_site = local_dict['games-site-location']
        self.pgn_site = local_dict['pgn-site-location']

    @staticmethod
    def init_config():
        ConfigData.local_config = ConfigData()

    @staticmethod
    def project_id():
        return "t4545-calendar-manager"

    @staticmethod
    def local_bucket_id():
        return "t4545-calendar-manager"

    @staticmethod
    def local_config_blob():
        return "runtime-parameters.json"

    @staticmethod
    def local_bucket_blob():
        return ConfigData.local_config.data_file

    @staticmethod
    def local_credential_blob():
        return ConfigData.local_config.credential_file

    @staticmethod
    def games_url():
        return ConfigData.local_config.games_site

    @staticmethod
    def pgn_base_url():
        return ConfigData.local_config.pgn_site

    @staticmethod
    def days_to_keep_events():
        return ConfigData.local_config.days_to_keep_events
