This implements a GCP cloud function that expects to be triggered by a pub/sub message

It builds shareable calendars that contain events for currently scheduled games for the T4545 league
Each calendar can track specific players, teams and/or divisions
This way, as events get scheduled they show up in a calendar for reference

it takes the following actions
- read existing calendar and event data from a bucket
- reads events from the scheduled games page
- any new events that should be tracked are added to the appropriate calendar(s)
- any events that have rolled of the calendar are removed from the appropriate calendar(s)

There is a single cloud function implemented, expects the action to be passed into it via the pub/sub message
the "normal" action is "update", although "init", "add_calendar" and "remove_calendar" are available

to setup for this environment:

install google cloud cli installer: https://cloud.google.com/sdk/docs/install
and authenticate for the project you are interested in 


build a conda env for you to use, just python=3.* as a starting point

install cloud client: pip install --upgrade google-cloud-storage

add functions-framework manually: pip install functions-framework

temp comment the first line of the requirements.txt file, then install the rest of the dependencies:

conda install --yes --file requirements.txt

todo
    read pubsub message contents and act accordingly
    better instrumentation (logging) and email on any kind of error
