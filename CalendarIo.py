import json
from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta

from LogDetail import LogDetail
from ConfigData import config_data_factory
from BucketIo import BucketIo


class CalendarIo:
    def __init__(self):
        self.SCOPES = ["https://www.googleapis.com/auth/calendar"]
        return

    @staticmethod
    def get_credentials_from_bucket():
        return BucketIo().read_data(config_data_factory().credential_file)

    @staticmethod
    def write_credentials_to_bucket(cred_dict):
        BucketIo().write_data(config_data_factory().credential_file, cred_dict)

    def get_credentials(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        cred_data = self.get_credentials_from_bucket()
        creds = Credentials.from_authorized_user_info(cred_data, self.SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self.write_credentials_to_bucket(json.loads(creds.to_json()))
        return creds

    def new_calendar(self, args):
        service = None
        new_cal_id = ""
        try:
            creds = self.get_credentials()
            service = discovery.build("calendar", "v3", credentials=creds)
        except Exception:
            LogDetail().print_log("Error",
                                  "Exception accessing calendar service - new_calendar: <" + args["name"] + "> ")

        try:
            body = {
                "kind": "calendar#calendar",  # Type of the resource ("calendar#calendar").
                "description": args["calName"],  # Description of the calendar. Optional.
                "summary": args["calName"],  # Title of the calendar.
                "timeZone": 'America/New_York',
                # The time zone of the calendar. (Formatted as an IANA Time Zone Database name, e.g. "Europe/Zurich".) Optional.
            }
            # cal_list_old = service.calendarList().list().execute()
            insert_rtn = service.calendars().insert(body=body).execute()
            # cal_list_new = service.calendarList().list().execute()

            new_cal_id = insert_rtn['id']

        except:
            LogDetail().print_log("Error", "Attempt to create new calendar failed: " + args["name"])
        return new_cal_id

    def delete_calendar(self, args):
        service = None
        try:
            creds = self.get_credentials()
            service = discovery.build("calendar", "v3", credentials=creds)
        except Exception:
            LogDetail().print_log("Error",
                                  "Exception accessing calendar service - delete_calendar: <" + args["name"] + "> ")
        try:
            service.calendars().delete(calendarId=args['access']["url"]).execute()

        except:
            LogDetail().print_log("Error", "Attempt to remove calendar failed: " + args["name"])
        return

    def remove_from_calendar(self, event, calendar):
        service = None
        try:
            creds = self.get_credentials()
            service = discovery.build("calendar", "v3", credentials=creds)
        except Exception:
            LogDetail().print_log("Error",
                                  "Exception accessing calendar service - add_to_calendar: <" + calendar["name"] + "> ")

        try:
            if "eventId" in event:
                service.events().delete(calendarId=calendar["access"]["url"], eventId=event["eventId"]).execute()
        except Exception:
            LogDetail().print_log("Error", "Attempt to delete event failed: " + event["eventId"])
        return 0

    def update_calendar_event(self, event, calendar):
        self.add_to_calendar(event, calendar)

    def add_to_calendar(self, event, calendar):
        service = None
        try:
            creds = self.get_credentials()
            service = discovery.build("calendar", "v3", credentials=creds)
        except Exception:
            LogDetail().print_log("Error",
                                  "Exception accessing calendar service - add_to_calendar: <" + calendar["name"] + "> ")

        event_time = datetime.strptime(event["time"], "%Y-%m-%dT%H:%M:00%z")
        end_time = event_time + timedelta(hours=2)

        event_start = event_time.strftime("%Y-%m-%dT%H:%M:00%z")  # Sat, Mar 16, 11:00
        event_end = end_time.strftime("%Y-%m-%dT%H:%M:00%z")  # Sat, Mar 16, 11:00

        description = 'Division ' + event["division"] + ' ' + event["result"]

        event_str = {
            'summary': 'T4545 Game - Round ' + event["round"] + ': ' + event["players"],
            'location': 'Internet Chess Club',
            'description': description,
            'start': {
                'dateTime': event_start,
                'timeZone': 'America/New_York',
            },
            'end': {  # add a 2 hour window
                'dateTime': event_end,
                'timeZone': 'America/New_York',
            },
            'recurrence': [
            ],
            'attendees': [
            ],
            'reminders': {
            },
        }
        try:
            if "old_id" in event.keys() and event["old_id"] is not None:
                saved_event = service.events().update(
                    calendarId=calendar["access"]["url"],
                    eventId=event["eventId"],
                    body=event_str).execute()
                assert saved_event["id"] == event["eventId"]
            else:
                saved_event = service.events().insert(calendarId=calendar["access"]["url"], body=event_str).execute()
                event["eventId"] = saved_event["id"]
        except Exception:
            LogDetail().print_log("Error",
                                  "Exception writing to calendar - add_to_calendar: <" + calendar["name"] + "> ")
        return 0

    def update_events(self, json_dict):
        removed_cals = []
        for cal in json_dict["calendars"]:
            if cal["status"] == "removed":
                removed_cals.append(cal)
            removed_ids = []
            for key in cal["events"]:
                event = cal["events"][key]
                if "status" in event and event["status"] == "removed":
                    # remove this id from the external calendar
                    self.remove_from_calendar(event, cal)
                    # add this to the removed_ids list
                    removed_ids.append(key)
                if "status" in event and event["status"] == "added":
                    # write the new event to the calendar
                    self.add_to_calendar(event, cal)
                    # clear metadata from the event
                    del cal["events"][key]["status"]
                if "status" in event and event["status"] == "updated":
                    # write the new event to the calendar
                    self.update_calendar_event(event, cal)
                    # clear metadata from the event
                    del cal["events"][key]["status"]
            for key in removed_ids:
                del cal["events"][key]

        for cal in removed_cals:
            json_dict["calendars"].remove(cal)

    @staticmethod
    def test_calendar(do_cal_io=True):
        calendar = {
            "name": "John TD",
            "access": {
                "url": "c_17d574477ec6a249e29e800a4a8d5aa693bd131651a1ba97953ec0ab0dc336d8@group.calendar.google.com",
                "credential": "SomeCred"
            }
        }
        event = {"players": "P1-P2", "time": "Sat, Mar 16, 11:00", "round": "1", "board": "3",
                 "division": "TestDivision"}

        if do_cal_io:
            CalendarIo().add_to_calendar(event, calendar)


if __name__ == '__main__':
    CalendarIo().test_calendar(False)
