from bs4 import BeautifulSoup
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
            for key in cal["events"]:
                cal["events"][key]["status"] = "loaded"

    @staticmethod
    def update_calendar(cal, args):
        LogDetail.LogDetail().print_log("log", "Editing calendar - " + cal["name"])
        Calendars.update_attribute_list(cal["players"], args["players"])
        Calendars.update_attribute_list(cal["divisions"], args["divisions"])
        Calendars.update_attribute_list(cal["teams"], args["teams"])

    @staticmethod
    def update_attribute_list(cur_list, update_string):
        cur_verb = ""
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

    def update_events(self, html_data):
        any_updated = False
        for cal in self.cal_dict["calendars"]:
            incoming = len(cal["events"])
            updated = 0
            discovered = 0
            written = 0
            removed = 0

            # Parse HTML page with BeautifulSoup
            soup = BeautifulSoup(html_data, 'html.parser')

            # Get the text content
            pairing_table = soup.find_all('table', {'class': 'sched'})
            pairings = pairing_table[0].find_all('tr')
            for tag in pairings:
                # read the elements of this row...
                pairing_attr = tag.find_all('td', recursive=False)
                if len(pairing_attr) == 0:
                    continue
                wPlayer = pairing_attr[4].text
                bPlayer = pairing_attr[6].text
                wTeam = pairing_attr[3].text
                bTeam = pairing_attr[7].text
                division = pairing_attr[0].text
                if (wTeam in cal["teams"] or bTeam in cal["teams"] or
                        wPlayer in cal["players"] or bPlayer in cal["players"] or
                        division in cal["divisions"]):
                    team_tag = wTeam + "-" + bTeam
                    player_tag = wPlayer.strip() + "-" + bPlayer.strip()
                    # print( player_tag+"-"+tag.find('td', {'class': 'result'}).text)
                    key = team_tag + ": " + player_tag

                    game_time = pairing_attr[2].text
                    real_time = game_time
                    round = pairing_attr[1].text
                    board = pairing_attr[8].text

                    # at this point, if the event doesn't exist at this place/time, write it
                    if key not in cal["events"]:
                        discovered = discovered + 1
                        LogDetail.LogDetail().print_log("event", "Writing new event - " + key)
                        new_event = {"players": player_tag, "time": game_time, "round": round, "board": board,
                                     "division": division}

                        cal["events"][key] = new_event
                        new_event["status"] = "updated"
                        written = written + 1
                        any_updated = True
                    else:
                        # at this point, the event already exists in the calendar
                        # if date is not the same (but is a valid date), then update the event
                        if cal["events"][key]["time"] == game_time:
                            cal["events"][key]["status"] = "validated"
                        else:
                            LogDetail.LogDetail().print_log("event", "Updating  event - " + key)
                            this_event = cal["events"][key]
                            this_event["time"] = game_time
                            this_event["old_id"] = this_event["eventId"]
                            this_event["status"] = "updated"

                            cal["events"][key] = new_event
                            updated = updated + 1
                            written = written + 1
                            any_updated = True

            for key in cal["events"]:
                this_event = cal["events"][key]
                if this_event["status"] == "loaded":
                    this_event["status"] = "removed"
                    any_updated = True
                    removed = removed + 1

            final = len(cal["events"])
            if self.print_cal_summary:
                LogDetail.LogDetail().print_log("Log", "For calendar " + cal["name"] +
                                                ": Incoming: " + str(incoming) +
                                                " Discovered: " + str(discovered) +
                                                " Updated: " + str(updated) +
                                                " Written: " + str(written) +
                                                " Deleted: " + str(removed) +
                                                " Final: " + str(final - removed))

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
        players = args["players"]  # list of string values
        divisions = args["divisions"]  # list of string values
        teams = args["teams"]  # list of string values

        newCal = {"name": name,
                  "access": {"url": cal_link, "credential": cal_cred},
                  "players": players, "divisions": divisions, "teams": teams,
                  "events": {}
                  }
        self.cal_dict["calendars"].append(newCal)

    def remove_calendar(self, names):
        for cal in self.cal_dict["calendars"]:
            if cal["name"] in names:
                cal["status"] = "removed"
                for key in cal["events"]:
                    this_event = cal["events"][key]
                    this_event["status"] = "removed"
