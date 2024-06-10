from urllib.request import Request

import functions_framework

import Calendar_IO
import Bucket_IO
import Games_IO
import Calendars
import base64
import json
from Games_IO import Games_IO

from LogDetail import LogDetail


# base config

def project_id():
    return "t4545-calendar-manager"


def local_bucket_id():
    return "t4545-calendar-manager"


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

            visible_games = Games_IO.load_games(games_url())
            updated = current_calendars.update_events(visible_games)

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
            LogDetail().print_log("Log", "Quit signal received - exiting!")
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


def do_basic_command(verb):
    this_msg = template_msg.copy()
    do_command(verb, this_msg)

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

def add_calendar(cal_name):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    do_command("add_calendar", this_msg)

def remove_calendar(cal_name):
    this_msg = template_msg.copy()
    this_msg["message"]["attributes"]["calName"] = cal_name
    do_command("remove_calendar", this_msg)

def get_command():
    match input("Please enter the number of the command you'd like to run:\n" +
          " 1 to display the current calendar configurations\n" +
          " 2 to run a regular update\n" +
          " 3 to edit a calendar configuration\n" +
          " 4 to add a new calendar\n" +
          " 5 to remove a calendar\n" +
          " 6 to init the entire managed structure\n" +
          " 7 to quit\n"
          ):
        case "1":
            return "display", None,None,None
        case "2":
            return "update", None,None,None
        case "3":
            calName = input("Enter the calendar name to edit:")
            action = input("Enter 'add' or 'remove':")
            option = input("Enter 'team', 'player', or 'division':")
            arg = input("Enter name of new or updated entity:")

            return action+"_"+option, calName, arg, None
        case "4":
            return "new_calendar", input("Enter the new calendar name:"), None,None
        case "5":
            return "remove_calendar", input("Enter the calendar name to remove:"), None,None
        case "6":
            return "init", None,None,None
        case "7":
            return "quit", None,None,None
        case _:
            print( "Didn't get that..." )
            return None,None,None,None





if __name__ == '__main__':

    done = False

    while not done:
        verb, cal_name, arg, entity = get_command()

        match verb:
            case "display":
                do_basic_command(verb)  # show structure before this action
            case "update":
                do_basic_command(verb)  # show structure before this action
            case "add_division":
                add_division(cal_name, arg)
            case "remove_division":
                remove_division(cal_name, arg)
            case "add_team":
                add_team(cal_name, arg)
            case "remove_team":
                remove_team(cal_name, arg)
            case "add_player":
                add_player(cal_name, arg)
            case "remove_player":
                remove_player(cal_name, arg)
            case "init":  # deletes all existing calendars
                do_basic_command(verb)
            case "add_calendar":  # adds an empty calendar to the structure
                add_calendar(cal_name)
            case "remove_calendar":  # removes a calendar (and cal events) from the structure
                remove_calendar(cal_name)
            case "quit":
                done = True
            case _:
                LogDetail().print_log("Error", "Unknown action <" + verb + ">")
