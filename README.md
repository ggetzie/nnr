# No Nonsense Recipes

Just recipes, no nonsense

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg)](https://github.com/pydanny/cookiecutter-django/)

[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

:License: MIT

https:/nononsense.recipes is an ad-free, subscription recipe website.

## Deploying

Setting up a fresh Ubuntu server. This uses scripts found in [homebin](https://github.com/ggetzie/homebin)

### Install prerequisites
Add the postgresql repositories and use a newer version than whatever apt has. [See here](https://www.postgresql.org/download/linux/ubuntu/)

Create a superuser in postgres for the main server user (probably 'ubuntu')

```
sudo su postgres
psql postgres
CREATE USER ubuntu WITH SUPERUSER;
\q
exit
```

Make sure TCP/IP connections with username/password are enabled for postgres.
For standard install edit files in `/etc/postgresql/15/main` (replace 15 with postgresql version used)
Edit `postgres.conf` to enable TCP/IP and `pg_hba.conf` to set allowed for nnr user.

Add the nginx, redis, supervisor and utility scripts
```   
sudo apt install redis, supervisor, nginx
git clone git@github.com:ggetzie/homebin.git
```     

### Create ssh key and link to github

[See here](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)

### Install uv

uv manages both the Python interpreter and the dependencies, so no system Python build is needed.

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone the repository, copy over .env file
```   
# on server
cd /usr/local/src/
git clone --recurse-submodules git@github.com:ggetzie/nnr.git

# on local
scp -i "nnr_server_key.pem" nnr_prod_keys ubuntu@nnr-server:/usr/local/src/nnr/.env
```
### Shared Python location (required)

The app runs as `nnr_user` under supervisor, but deploys run as a different user.
`uv` installs Python under the *installing* user's home by default, and `.venv/bin/python`
is a symlink to it -- so `nnr_user` cannot traverse to it and gunicorn dies with
`bad interpreter: Permission denied`. Install Python somewhere both users can reach:

```
sudo mkdir -p /opt/uv/python
sudo chown "$USER" /opt/uv/python
echo 'export UV_PYTHON_INSTALL_DIR=/opt/uv/python' | sudo tee /etc/profile.d/uv.sh
export UV_PYTHON_INSTALL_DIR=/opt/uv/python
```

Set this **before** the first `uv sync`. If a venv already exists pointing at the wrong
place, `rm -rf .venv` first -- the interpreter path is fixed when the venv is created and
`uv sync` will not repoint it.

Verify with `readlink -f .venv/bin/python`; it should be under `/opt/uv/python`.

### Install dependencies and build the frontend assets

```
cd /usr/local/src/nnr
uv sync --frozen              # installs the pinned Python and creates .venv
uv run --group build scripts/build_assets.py
```

`uv sync --frozen` installs exactly what `uv.lock` records and must be re-run on every deploy --
`gunicorn_start.bash` execs `.venv/bin/gunicorn` directly.

### Create a user
```
setup_user nnr_user
```

### Export environment variables from .env file
```
source export_dotenv nnr
```

### Setup Database

```
setup_db $DB_USER $DB_NAME $nnr_DB_PW
psql nnr_db < nnr_db_prod.pgsql
```

### Link supervisor and nginx configurations

```
link_srv nnr production
```

### Enable ssl with certbot
See [instructions](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal)
Note AWS Lightsail does not enable port 443 by default. Go to the networking tab in the Lightsail dashboard to open it.

### configure cron job
Note server time is UTC. Run rotd once per day at 7am EST (UTC-5).

`rotd.sh` runs the `choose_rotd` management command, which selects the recipe of the day,
clears the cached homepage fragment and posts the tweet. No Go toolchain is needed on the
server -- the Go lambda that used to do this was redundant and has been removed.

```
m h  dom  mon  dow  command
0 12 *    *    *    /usr/local/src/nnr/recipes/management/rotd.sh
```

`rotd.sh` writes its own output to `logs/rotd.log` (timestamped, one block per run, with the
exit status) rather than relying on cron, which mails failures to the crontab owner and
silently discards them when no MTA is installed. Check that file first when the recipe of
the day does not change. The script exits nonzero on failure, so `journalctl -t CRON` records
the failed run too.

