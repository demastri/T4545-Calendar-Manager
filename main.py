import functions_framework
import Calendar_IO
import Bucket_IO
import Games_IO
import Calendars
from time import sleep

from LogDetail import LogDetail


# base config

def project_id():
    return "t4545-calendar-manager"


def local_bucket_id():
    return "jpd-t4545-calendar-manager"


def local_bucket_blob():
    return "config.json"


def local_credential_blob():
    return "token.json"


def games_url():
    return "http://team4545league.org/tournament/games.html"


def run_task(task, args):
    done = False

    match task:
        case "update":
            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())

            game_data = Games_IO.Games_IO().get_games_data(games_url())
            updated = current_calendars.update_events(game_data)

            if updated:
                shared_calendars = Calendar_IO.Calendar_IO(project_id(), local_bucket_id(), local_credential_blob())
                shared_calendars.update_events(current_calendars.cal_dict)
                bucket.write_data(current_calendars.cal_dict)
                LogDetail().print_log("Log", "Bucket overwritten")
            else:
                LogDetail().print_log("Log", "No updates found, bucket not overwritten")

        case "init":  # deletes all existing calendars
            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())
            cal_names = []
            for cal in current_calendars.cal_dict["calendars"]:
                cal_names.append(cal["name"])
            run_task("remove_calendar", cal_names)
            LogDetail().print_log("Log", "Bucket overwritten on reset of all calendars")

        case "add_calendar":  # adds an empty calendar to the structure
            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())
            current_calendars.add_calendar(args)
            # the new calendar should not have events, so calendarIO is not required
            bucket.write_data(current_calendars.cal_dict)
            LogDetail().print_log("Log", "Bucket overwritten to add calendar " + args[0])

        case "remove_calendar":  # removes a calendar (and cal events) from the structure
            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())
            current_calendars.remove_calendar(args)

            shared_calendars = Calendar_IO.Calendar_IO(project_id(), local_bucket_id(), local_credential_blob())
            shared_calendars.update_events(current_calendars.cal_dict)
            bucket.write_data(current_calendars.cal_dict)
            LogDetail().print_log("Log", "Bucket overwritten on removal of calendars:" + ' '.join(args))

        case "quit":
            LogDetail().print_log("Log", "Quit signal received - exiting")
            done = True

    return done


@functions_framework.http
def hello_http(request):
    run_task("update", [])
    return "Success"
