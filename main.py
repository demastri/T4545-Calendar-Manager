from urllib.request import Request

import functions_framework

import Calendar_IO
import Bucket_IO
import Games_IO
import Calendars
import base64
import json

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
        case "display":
            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())
            for cal in current_calendars.cal_dict["calendars"]:
                print(cal)
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

        case "edit":  # updates calendar definitions - does not update definitions
            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())
            for cal in current_calendars.cal_dict["calendars"]:
                if "calName" in args and cal["name"] == args["calName"]:
                    Calendars.Calendars.update_calendar(cal, args)
                    LogDetail().print_log("Log", args["calName"] + "-Teams:" + str(cal["teams"]))
                    LogDetail().print_log("Log", args["calName"] + "-Divisions:" + str(cal["divisions"]))
                    LogDetail().print_log("Log", args["calName"] + "-Players:" + str(cal["players"]))
            bucket.write_data(current_calendars.cal_dict)
            LogDetail().print_log("Log", "Bucket overwritten on edited calendar(s) ")

        case "add_calendar":  # adds an empty calendar to the structure
            exists = False
            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())
            for cal in current_calendars.cal_dict["calendars"]:
                if "calName" in args and cal["name"] == args["calName"]:
                    exists = True

            if not exists:
                created = False
                args["name"] = args["calName"]
                args["url"] = ""
                args["cred"] = ""
                # create a new calendar
                newCalId = Calendar_IO.Calendar_IO(project_id(), local_bucket_id(),
                                                   local_credential_blob()).new_calendar(args)
                # get URL / credential for new calendar

                if newCalId != "":
                    args["url"] = newCalId
                    args["cred"] = "Some cred"
                    current_calendars.add_calendar(args)
                    # the new calendar should not have events, so calendarIO is not required
                    bucket.write_data(current_calendars.cal_dict)
                    LogDetail().print_log("Log", "Bucket overwritten to add calendar " + args["name"])
                else:
                    # send email with failure
                    LogDetail().print_log("Log",
                                          "Request to create calendar failed, bucket not overwritten: " + args["name"])
            else:
                # send email with failure
                LogDetail().print_log("Log",
                                      "Request to add existing calendar, bucket not overwritten: " + args["name"])

        case "remove_calendar":  # removes a calendar (and cal events) from the structure
            # can change this - just remove the structure from our cal list and delete the calendar from google

            bucket = Bucket_IO.Bucket_IO(project_id(), local_bucket_id(), local_bucket_blob())
            current_calendars = Calendars.Calendars(bucket.read_data())

            # this is not a list
            cal_name = args["calName"]
            removeList = [x for x in current_calendars.cal_dict["calendars"] if x["name"] in cal_name]

            this_calIO = Calendar_IO.Calendar_IO(project_id(), local_bucket_id(), local_credential_blob())
            for cal in removeList:
                this_calIO.delete_calendar(cal)

            current_calendars.remove_calendar([cal_name])
            bucket.write_data(current_calendars.cal_dict)
            LogDetail().print_log("Log", "Bucket overwritten on removal of calendars: " + cal_name)

        case "quit":
            LogDetail().print_log("Log", "Quit signal received - exiting")
            done = True

        case _:
            LogDetail().print_log("Error", "Unknown action <" + task + ">")

    return done


@functions_framework.http
def hello_http(request):
    data = request.data.decode("ascii")
    data = json.loads(data)

    action = data["message"]["data"]
    action = base64.b64decode(action).decode("ascii")
    args = {}
    if "attributes" in data["message"]:
        args = data["message"]["attributes"]

    run_task(action, args)
    return "Success"


sample_upd_msg = {
    "subscription": "projects/t4545-calendar-manager/subscriptions/eventarc-us-central1-t4545-calendar-task-ps-640276-sub-622",
    "message": {
        "data": "dXBkYXRl",
        "attributes": {
            "calName": "John Testing Cal",
            "teams": "",
            "divisions": "--add U1300&nbsp;Planetary_Playoffs",
            "players": "--remove Rookmaster --add Gojira",
            "respondEmail": "john@demastri.com"
        },
        "publish_time": "2024-03-29T21:28:53.78Z",
        "message_id": "10811014301783647",
        "publishTime": "2024-03-29T21:28:53.78Z",
        "messageId": "10811014301783647"
    }
}

sample_add_msg = {
    "subscription": "projects/t4545-calendar-manager/subscriptions/eventarc-us-central1-t4545-calendar-task-ps-640276-sub-622",
    "message": {
        "data": "dXBkYXRl",
        "attributes": {
            "calName": "John Testing Cal",
            "teams": [],
            "divisions": [],
            "players": [],
            "respondEmail": "john@demastri.com"
        },
        "publish_time": "2024-03-29T21:28:53.78Z",
        "message_id": "10811014301783647",
        "publishTime": "2024-03-29T21:28:53.78Z",
        "messageId": "10811014301783647"
    }
}

if __name__ == '__main__':
    """
    update takes no parameters, goes out to games page and updates any existing calendars
    "edit" takes the following parameters as keys in the attributes section:
        calendarName: name of the calendar to update
        semantics for each list:
            --verb arg --verb arg 
            verbs operated on in order
            allowed verbs are
                --clear     takes no arg - resets list to empty
                --add       takes one arg - adds the given item to the list if not there already
                --remove    takes one arg - removes the given item to the list if it's there already
                neither --add nor --remove care if no action is taken if --add is there or --remove isn't
            an empty list takes no action, although all three keys should be present        
        
        teams and divisions can have spaces, and division names have the rating and &nbsp before the name
            replace any ' ' with '_' in this message (haven't seen a team/div with an underscore...)
            div and playoff names are "controlled", and usernames are restricted to alpha+'-', to just teams...
            so a playoff division could be named "U1300&nbsp;Erg_Playoffs" and a season "U1500&nbsp;Mars"
        add 1 team, remove 1 player, leave divisions alone:
        "calName" : "some cal"
        "teams" : "--add teamName",
        "players" : "--remove playerID",
        "divisions" : "" 
        
    """
    #testing_action = "add_calendar"
    testing_action = "remove_calendar"
    #testing_action = "display"
    # takes calName: name, respondEmail: email, teams: players: divisions:
    # should check if there's already a calendar with this name
    # create if possible and acquire the sharable URL
    # and send a reply email to the respondEmail with success / failure
    # testing_action = "remove_calendar"
    # takes calName: name as attribute for cal/events to remove
    # should actually delete the calendar as well
    # testing_action = "update"
    # testing_action = "edit"

    sample_msg = sample_add_msg

    testing_action = base64.b64encode(testing_action.encode("ascii"))

    sample_msg["message"]["data"] = testing_action.decode("ascii")
    if "attributes" not in sample_msg["message"]:
        sample_msg["message"]["attributes"] = {}

    hello_http(Request(url="http://x.com", data=json.dumps(sample_msg).encode("ascii")))
