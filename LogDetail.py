from datetime import datetime
class LogDetail:
    def __init__(self):
        return

    def get_logtime(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def print_log(self, log_type, message):
        print("{\""+log_type+"\" : \"" + self.get_logtime() + " - " + message + "\"}")

