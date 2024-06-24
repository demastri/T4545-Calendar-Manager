import BucketIo

project_id = "t4545-calendar-manager"
bucket_id = "t4545-calendar-manager"


class ConfigData(object):

    def __init__(self):
        # if you load this from the local file system, you have to deploy a new version for a param change
        # if you load from Cloud Storage, you can update the file in place, but you have to know where to look
        # the latter seems is slightly more flexible for parameter changes that don't require other code changes

        self.config_file = "runtime-parameters.json"

        local_dict = (BucketIo.BucketIo().read_data(self.config_file))

        self.credential_file = local_dict['credential-file']
        self.data_file = local_dict['data-file']
        self.games_site = local_dict['games-site-location']
        self.pgn_site = local_dict['pgn-site-location']
        self.days_to_keep_events = local_dict['days-to-keep-events']
        self.log_calendar_summary = local_dict['log-calendar-summary']


def config_data_factory(_singleton=ConfigData()):
    return _singleton
