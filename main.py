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
                if "calName" in args and (cal["name"] == args["calName"] or "*" == args["calName"]):
                    Calendars.Calendars.edit_calendar(cal, args)
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


template_msg = {
    "subscription": "projects/t4545-calendar-manager/subscriptions/eventarc-us-central1-t4545-calendar-task-ps-640276-sub-622",
    "message": {
        "data": "",
        "attributes": {
            "calName": "",
            "teams": "",
            "divisions": "",
            "players": "",
            "respondEmail": ""
        },
        "publish_time": "2024-03-29T21:28:53.78Z",
        "message_id": "10811014301783647",
        "publishTime": "2024-03-29T21:28:53.78Z",
        "messageId": "10811014301783647"
    }
}

sample_upd_msg = {
    "subscription": "projects/t4545-calendar-manager/subscriptions/eventarc-us-central1-t4545-calendar-task-ps-640276-sub-622",
    "message": {
        "data": "dXBkYXRl",
        "attributes": {
            "calName": "Reyk Calendar",
            "teams": "--remove Reykjavikings_III --add STC_Silver",
            "divisions": "--remove STC_Silver",
            "players": "",
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
            "calName": "*",
            "teams": "",
            "divisions": "",
            "players": "",
            "respondEmail": "john@demastri.com"
        },
        "publish_time": "2024-03-29T21:28:53.78Z",
        "message_id": "10811014301783647",
        "publishTime": "2024-03-29T21:28:53.78Z",
        "messageId": "10811014301783647"
    }
}

def do_command( verb, msg ):
    action = base64.b64encode(verb.encode("ascii"))
    msg["message"]["data"] = action.decode("ascii")
    hello_http(Request(url="http://x.com", data=json.dumps(msg).encode("ascii")))
    return

def add_team( cal_name, team ):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    wire_team = team.replace(" ", "_")
    this_msg["message"]["attributes"]["teams"] = "--add "+wire_team
    do_command("edit", this_msg)

def remove_team( cal_name, team ):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    wire_team = team.replace(" ", "_")
    this_msg["message"]["attributes"]["teams"] = "--remove "+wire_team
    do_command("edit", this_msg)

def add_player( cal_name, player ):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    wire_player = player.replace(" ", "_")
    this_msg["message"]["attributes"]["players"] = "--add "+wire_player
    do_command("edit", this_msg)

def remove_player( cal_name, player ):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    wire_player = player.replace(" ", "_")
    this_msg["message"]["attributes"]["players"] = "--remove "+wire_player
    do_command("edit", this_msg)

def add_division( cal_name, div ):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    wire_div = div.replace(" ", "_")
    this_msg["message"]["attributes"]["divisions"] = "--add " + wire_div
    do_command("edit", this_msg)


def remove_division( cal_name, div ):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    wire_div = div.replace(" ", "_")
    this_msg["message"]["attributes"]["divisions"] = "--remove "+wire_div
    do_command("edit", this_msg)

def do_update():
    this_msg = template_msg.copy()
    do_command("update", this_msg)

def do_display():
    this_msg = template_msg.copy()
    do_command("display", this_msg)


if __name__ == '__main__':

    # added helper functions to make testing and maintenance easier:
    do_display()    # show structure before this action

    # do some combination of these actions as needed...
    this_cal = "John TD"
    #add_player( this_cal, "TestPlayer")
    #remove_player( this_cal, "TestPlayer")

    add_team( this_cal, "TestTeam")
    do_display()    # show structure between the two actions, as needed...
    remove_team( this_cal, "TestTeam")

    #add_division( this_cal, "TestDiv")
    #remove_division( this_cal, "TestDiv")

    #do_update() # or just read data from the site...

    do_display()    # show structure after this action
