#!/bin/bash
NAME="nnr"
DJANGODIR="/usr/local/src/nnr/"
SOCKFILE="/usr/local/src/nnr/run/gunicorn.sock"
USER=nnr_user
GROUP=webapps
NUM_WORKERS=3
TIMEOUT=120
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_WSGI_MODULE=config.wsgi

echo "Starting $NAME as `whoami`"

# The virtualenv is managed by uv and lives at $DJANGODIR/.venv.
# Deploys must run `uv sync --frozen` before restarting this program.
cd $DJANGODIR

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# The venv's interpreter is a symlink into wherever uv installed Python. If that
# is under the deploying user's home directory, this user cannot traverse to it
# and the exec below fails with "bad interpreter: Permission denied". Fail here
# instead, with something actionable.
VENV_PY="${DJANGODIR}.venv/bin/python"
if ! "$VENV_PY" -c "" 2>/dev/null; then
    echo "ERROR: $VENV_PY is not executable as $(whoami)." >&2
    echo "It resolves to: $(readlink -f "$VENV_PY" 2>/dev/null || echo "<unresolvable>")" >&2
    echo "If that path is under another user's home, reinstall Python somewhere shared:" >&2
    echo "  export UV_PYTHON_INSTALL_DIR=/opt/uv/python" >&2
    echo "  uv python install && rm -rf .venv && uv sync --frozen" >&2
    exit 1
fi

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start you Django Unicorn 
# Programs meant to be run under supervisor should not
# daemonize themselves.
# (do not use --daemon)

exec "${DJANGODIR}.venv/bin/gunicorn" ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --timeout $TIMEOUT \
    --user=$USER --group=$GROUP \
    --bind 127.0.0.1:8005 \
    --log-level=debug \
    --log-file=-

