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

### Install Python 3.11+
[See here](https://tiltingatwindmills.dev/how-to-install-an-alternate-python-version/)

### Clone the repository, copy over .env file
```   
# on server
cd /usr/local/src/
git clone --recurse-submodules git@github.com:ggetzie/nnr.git

# on local
scp -i "nnr_server_key.pem" nnr_prod_keys ubuntu@nnr-server:/usr/local/src/nnr/.env
```
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

### Install go and build recipe of the day
```
update_go 1.19.3
cd /usr/local/src/nnr/awslambda/rotd
mkdir build
go build -o build/rotd rotd.go
```

### configure cron job
Note server time is UTC. Run rotd once per day at 7am EST (UTC-5)

```
m h  dom  mon  dow  command
0 12 *    *    *    /usr/local/src/nnr/recipes/management/rotd.sh
```

