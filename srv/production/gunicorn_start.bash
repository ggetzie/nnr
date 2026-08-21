#!/bin/bash
NAME="nnr"
DJANGODIR="/usr/local/src/nnr/"
SOCKFILE="/usr/local/src/nnr/run/gunicorn.sock"
USER=nnr_user
GROUP=webapps
NUM_WORKERS=3
TIMEOUT=120
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_WSGI_MODULE=config.wsgi

echo "Starting $NAME as `whoami`"

# The virtualenv is managed by uv and lives at $DJANGODIR/.venv.
# Deploys must run `uv sync --frozen` before restarting this program.
cd $DJANGODIR

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start you Django Unicorn 
# Programs meant to be run under supervisor should not
# daemonize themselves.
# (do not use --daemon)

exec /usr/local/src/nnr/.venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --timeout $TIMEOUT \
    --user=$USER --group=$GROUP \
    --bind 127.0.0.1:8000 \
    --log-level=warning \
    --log-file=-

