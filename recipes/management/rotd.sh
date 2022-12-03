#!/bin/bash

cd /usr/local/src/nnr
source /usr/local/src/env/nnr/bin/activate
# load environment variables from .env file
source $HOME/bin/export_dotenv nnr
# use --test flag to run locally from command line
/usr/local/src/nnr/awslambda/rotd/build/rotd --test
./manage.py choose_rotd