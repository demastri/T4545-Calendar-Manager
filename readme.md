This implements a GCP cloud function that expects to be triggered by a pub/sub message

It builds shareable calendars that contain events for currently scheduled games for the T4545 league

Each calendar can track specific players, teams and/or divisions

This way, as events get scheduled they show up in a calendar for reference

The internal tracking structure is stored in a GCP CS bucket that holds a list of entries with details about the 
calendar being tracked, including url for the calendar and ids and timing of all currently known events
- this means you can use an existing calendar, and this will not touch your other existing entries
- if you do this, be careful, don't delete your calendar, because that will remove it from google...
- of course, if you take this code and try to implement / extend it, you'll do it in your own calendar
space ...not mine, lol

There is a single cloud function implemented, expects the action to be passed into it via the pub/sub message in the 
["message"]["data"] entry (as a base64 encoded string). 

The normal action is "update", although "init", "add_calendar", "remove_calendar" and "edit" are available

Also - current code doesn't use respondEmail for anything...
thinking of putting a simple self-service site that lets people add/remove/edit their own calendars, and this
would be one way to track/notify people asking for service.  Until that site exists, looks like
the cloud function is sufficient for all normal actions, and any updates can be run from the IDE
as needed...  we're nominally live - 4-28-24

"init" removes all events / calendars from the bucket and Google Calendars
- calls "remove_calendar" for all known calendars

"update" takes the following actions (with no other parameters used)
- read existing calendar and event data from a bucket
- reads events from the scheduled games page
- any new events that should be tracked are added to the appropriate calendar(s)
- any events that have rolled of the calendar are removed from the appropriate calendar(s)

"add_calendar" takes one attribute parameter named "calName" and:
- checks if we're already managing a calendar with that name
- if so, log that error and quit 
- otherwise create the calender - in my personal calendar space :(
- set up the calendar structure
- rewrite the bucket and log success
- note, unlike "edit" the values in the teams++ are just lists of string entries to be added

"remove_calendar" takes one attribute parameter named "calName" and:
- checks if we're already managing a calendar with that name
- if so, remove it from google, and update the internal tracking structure 
- rewrite the bucket and log success

"edit" allows you to update the teams / players / division / respondEmail for any calendar
- takes "calName" as the calendar to modify ('*' is a valid wildcard)
- "teams" / "players" / "division" / "respondEmail" are valid keys for attributes
- you can "--add xxxyyy"  "--clear" or "--remove xxxyyy" from any list
- can have multiple entries in a line "--clear --add gojira"  execute in l/r order
- if respondEmail value is not "", the value provided overwrites that in ["access"]["respondEmail"]
- NOTE - there is goofiness in the handling of &nbsp; esp in division names - take a look at the code for more detail
- should be able to specify them as spaces in msgs as you'd expect, and the code just works

Check 'main.py' for test code and usage examples at the end of the file

- it 'the real world', the entry point hello_http() is called when a pubsub message is generated with its contents and acts accordingly
- currently, the cloud function only always calls with 'update' as the verb
- remember that the pubsub data always has the verb as base64 encoded in the msg["message"]["data"] location, while attributes are _unencoded_ plaintext key/value pairs in the msg["message"]["attributes"] location   

to setup for this environment:

install google cloud cli installer: https://cloud.google.com/sdk/docs/install
and authenticate for the project you are interested in 

build a conda env for you to use, just python=3.* as a starting point

install cloud client: pip install --upgrade google-cloud-storage

add functions-framework manually: pip install functions-framework

temp comment the first line of the requirements.txt file, then install the rest of the dependencies:

conda install --yes --file requirements.txt

