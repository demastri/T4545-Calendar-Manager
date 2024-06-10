from bs4 import BeautifulSoup
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

            """
                <tr>
                <tr><td class="sched">U1500&nbsp;<a href="../tournament/t100/t100round4.html#Gibson">Gibson</a></td><td class="sched">4</td>
                <td class="schedb">Sat, Jun 08, 15:00</td><td class="sched">Fishers of Men - Kings Army</td><td class="schedb_nrb" style="text-align:right">BIRDSMAN</td>
                <td class="schedbc_nhb"><a href ="../pgnplayer/pgnplayer.php?ID=28412&amp;Board=3">1:0</a></td><td class="schedb_nlb">cayo89</td><td class="sched">Jousting Knights U1500</td>
                <td class="sched">3</td></tr>

                    <td class="sched">U1500&nbsp;<a href="../tournament/t100/t100round4.html#Habbanya">Habbanya</a></td>
                    <td class="sched">4</td>
                    <td class="schedb">Sat, Jun 08, 21:00</td>
                    <td class="sched">Valar Morghulis U1500</td>
                    <td class="schedb_nrb" style="text-align:right">seattleblues</td>
                    
                    this could either be empty or have a result and link similar to as shown here:  
                    <td class="schedbc_nhb"><a href ="../pgnplayer/pgnplayer.php?ID=28412&amp;Board=3">1:0</a></td>
                    <td class="schedbc_nhb">-</td>
                    
                    <td class="schedb_nlb">Electryon</td>
                    <td class="sched">Dragons</td>
                    <td class="sched">4</td>
                    </tr>
            """

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

                gameLinkCell = pairing_attr[5]
                result_string = Games_IO.getPGNOrResultFromCell(gameLinkCell)
                gameHasResult = result_string != ""

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
                    new_event = {"players": player_tag, "time": game_time, "round": round, "board": board,
                                 "division": division}
                    if key not in cal["events"]:
                        discovered = discovered + 1
                        LogDetail.LogDetail().print_log("event", "Writing new event - " + key)

                        cal["events"][key] = new_event
                        new_event["status"] = "updated"
                        written = written + 1
                        any_updated = True
                    else:
                        # at this point, the event already exists in the calendar
                        # if date is not the same (but is a valid date), then update the event
                        # or, if the game has now been played, get the pgn and update the game

                        sameTime = cal["events"][key]["time"] == game_time
                        eventHasResult = ("result" in cal["events"][key].keys())

                        if sameTime and eventHasResult == gameHasResult:
                            cal["events"][key]["status"] = "validated"
                        else:
                            this_event = cal["events"][key]
                            if not sameTime:
                                LogDetail.LogDetail().print_log("event", "Updating event time- " + key)
                                this_event["time"] = game_time
                                this_event["old_id"] = this_event["eventId"]
                                this_event["status"] = "updated"
                            if eventHasResult != gameHasResult:
                                LogDetail.LogDetail().print_log("event", "Updating game result - " + key)


                                result_string = Games_IO.getPGNOrResultFromCell(gameLinkCell)
                                if result_string == "" and eventHasResult:
                                    this_event["old_id"] = this_event["eventId"]
                                    del this_event["result"]
                                    this_event["status"] = "updated"

                                if result_string != "" and (not eventHasResult or result_string != this_event["result"]):
                                    this_event["old_id"] = this_event["eventId"]
                                    this_event["result"] = result_string
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
                    event_time = Calendar_IO.get_actual_time_from_shown_time(this_event["time"])
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
