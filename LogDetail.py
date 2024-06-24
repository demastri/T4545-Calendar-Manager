import logging
from datetime import datetime


class LogDetail:
    def __init__(self):
        return

    @staticmethod
    def get_logtime():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def print_log(self, log_type, message):
        match log_type:
            case "Error":
                print("{\""+log_type+"\" : \"" + self.get_logtime() + " - " + message + "\"}")
                logging.error(RuntimeError(self.get_logtime() + " - " + message))
            case _:
                print("{\""+log_type+"\" : \"" + self.get_logtime() + " - " + message + "\"}")
