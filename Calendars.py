from datetime import datetime, timedelta
import pytz
from Games_IO import Games_IO
from Calendar_IO import Calendar_IO
import LogDetail

class Calendars:

    def __init__(self, cal_dict):
        self.cal_dict = cal_dict

        self.print_cal_summary = False

        # make sure each event has a status tag - set to loaded - can be set to validated or updated
        # if it's still "loaded" at the end of the update, then it's been removed from the source
        # also make sure each calendar has a status tag - set to loaded
        # if it's still "deleted" at the end of the update, then it's been removed
        for cal in self.cal_dict["calendars"]:
            cal["status"] = "loaded"
            no_event_id = []
            for key in cal["events"]:
                if( "eventId" not in cal["events"][key]):
                    no_event_id.append(key)
                cal["events"][key]["status"] = "loaded"
                if "result" not in cal["events"][key].keys():
                    cal["events"][key]["result"] = ""
            for k in no_event_id:
                del cal["events"][k]


    @staticmethod
    def edit_calendar(cal, args):
        LogDetail.LogDetail().print_log("log", "Editing calendar - " + cal["name"])
        Calendars.update_attribute_list(cal["players"], args["players"])
        Calendars.update_attribute_list(cal["divisions"], args["divisions"])
        Calendars.update_attribute_list(cal["teams"], args["teams"])
        if args["respondEmail"] != "":
            cal["access"]["respondEmail"] = args["respondEmail"]

    @staticmethod
    def update_attribute_list(cur_list, update_string):
        cur_verb = ""
        if update_string == "":
            return
        for val in update_string.split():
            val = val.replace("&nbsp;", "\xa0")
            val = val.replace("_", " ")
            match cur_verb:
                case "":
                    cur_verb = val
                case "--add":
                    LogDetail.LogDetail().print_log("log", "adding - " + val)
                    if val not in cur_list:
                        cur_list.append(val)
                    cur_verb = ""
                case "--clear":
                    LogDetail.LogDetail().print_log("log", "clearing list")
                    cur_list.clear()
                    cur_verb = val
                case "--remove":
                    LogDetail.LogDetail().print_log("log", "removing - " + val)
                    while val in cur_list:
                        cur_list.remove(val)
                    cur_verb = ""

    def update_events(self, visible_games):
        any_updated = False

        for cal in self.cal_dict["calendars"]:
            incoming = len(cal["events"])
            updated = 0
            discovered = 0
            written = 0
            removed = 0

            for g in visible_games:
                if (g.whiteTeam in cal["teams"] or g.blackTeam in cal["teams"] or
                        g.whitePlayer in cal["players"] or g.blackPlayer in cal["players"] or
                        g.division in cal["divisions"]):

                    # at this point, if the event doesn't exist at this place/time, write it
                    new_event = {"players": g.player_tag(), "time": g.game_time.strftime("%Y-%m-%dT%H:%M:00%z"), "round": g.round, "board": g.board,
                                 "division": g.division, "result": "-"}
                    if g.game_key() not in cal["events"].keys():
                        discovered = discovered + 1
                        LogDetail.LogDetail().print_log("event", "Writing new event - " + g.game_key())

                        cal["events"][g.game_key()] = new_event
                        new_event["status"] = "added"
                        written = written + 1
                        any_updated = True
                    else:
                        # at this point, the event already exists in the calendar
                        # if date is not the same (but is a valid date), then update the event
                        # or, if the game has now been played, get the pgn and update the game

                        same_time = cal["events"][g.game_key()]["time"] == g.game_time.strftime("%Y-%m-%dT%H:%M:00%z")
                        same_game_result = cal["events"][g.game_key()]["result"] == g.result

                        if same_time and same_game_result:
                            cal["events"][g.game_key()]["status"] = "validated"
                        else:
                            this_event = cal["events"][g.game_key()]
                            if not same_time:
                                LogDetail.LogDetail().print_log("event", "Updating event time- " + g.game_key())
                                this_event["time"] = g.game_time.strftime("%Y-%m-%dT%H:%M:00%z")
                                this_event["old_id"] = this_event["eventId"]
                                this_event["status"] = "updated"
                            if not same_game_result:
                                LogDetail.LogDetail().print_log("event", "Updating game result - " + g.game_key())
                                this_event["old_id"] = this_event["eventId"]
                                this_event["result"] = g.result
                                this_event["status"] = "updated"

                            if this_event["status"] == "updated":
                                updated = updated + 1
                                written = written + 1
                                any_updated = True

            for key in cal["events"]:
                this_event = cal["events"][key]
                if "status" in this_event and this_event["status"] == "loaded":
                    days_to_linger = 3
                    # additional "timeout" check - say n days after the game was scheduled?
                    tz = pytz.utc
                    comparable_now = datetime.now(tz)
                    event_time = datetime.strptime(this_event["time"], "%Y-%m-%dT%H:%M:00%z")
                    rolloff_time = (event_time+timedelta(days=days_to_linger)).astimezone(tz)


                    if comparable_now > rolloff_time:
                        LogDetail.LogDetail().print_log("Log",
                            "Removing event after timeout - removed from site, was in calendar " + cal["name"] + " - " + key + " scheduled at " + this_event["time"] )

                        this_event["status"] = "removed"
                        any_updated = True
                        removed = removed + 1
                    else:
                        LogDetail.LogDetail().print_log("Log",
                            "Waiting for event to timeout - removed from site, still in calendar " + cal["name"] + " - " + key + " scheduled at " + this_event["time"] )

            if self.print_cal_summary:
                LogDetail.LogDetail().print_log("Log", "For calendar " + cal["name"] +
                                                ": Incoming: " + str(incoming) +
                                                " Discovered: " + str(discovered) +
                                                " Updated: " + str(updated) +
                                                " Written: " + str(written) +
                                                " Deleted: " + str(removed) )

        return any_updated

    def clear_all_calendars(self):
        for cal in self.cal_dict["calendars"]:
            for key in cal["events"]:
                this_event = cal["events"][key]
                this_event["status"] = "removed"

    def remove_all_calendars(self):
        for cal in self.cal_dict["calendars"]:
            cal["status"] = "removed"

    def add_calendar(self, args):
        name = args["name"]  # single value
        cal_link = args["url"]  # single value
        cal_cred = args["cred"]  # single value
        cal_email = args["respondEmail"]  # single value

        if args["players"] == "":  # list of string values - as a string...
            players = []
        else:
            players = args["players"].split()
        if args["divisions"] == "":  # list of string values - as a string...
            divisions = []
        else:
            divisions = args["divisions"].split()
        if args["teams"] == "":  # list of string values - as a string...
            teams = []
        else:
            teams = args["teams"].split()

        newCal = {"name": name,
                  "access": {"url": cal_link, "credential": cal_cred, "respondEmail": cal_email},
                  "players": players, "divisions": divisions, "teams": teams,
                  "events": {}
                  }
        self.cal_dict["calendars"].append(newCal)

    def remove_calendar(self, names):
        self.cal_dict["calendars"] = [x for x in self.cal_dict["calendars"] if x["name"] not in names]
