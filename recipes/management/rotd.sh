#!/bin/bash

cd /usr/local/src/nnr
source /usr/local/src/env/nnr/bin/activate
source $HOME/bin/export_dotenv nnr
# use local option
/usr/local/src/nnr/awslambda/rotd/build/rotd --test
./manage.py choose_rotd