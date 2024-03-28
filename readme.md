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
