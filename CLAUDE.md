# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`nnr` is the Django site behind [nononsense.recipes](https://nononsense.recipes) — an ad-free,
subscription (Stripe) recipe site, generated originally from Cookiecutter Django. Postgres +
Redis + gunicorn/nginx/supervisor on a single Ubuntu host (AWS Lightsail); media and static
files go to S3/CloudFront in production. Two Go AWS Lambdas live under `awslambda/`.

## Commands

Dependencies are managed by **uv** (`pyproject.toml` + `uv.lock`, Python pinned by
`.python-version`). `uv sync` creates `.venv`; there is no `requirements.txt`. Environment
variables come from `.env` in the repo root, read by `django-environ` at settings import —
every `manage.py` invocation needs it.

```bash
uv sync                            # runtime + dev deps
uv sync --group build              # adds the asset-build tools

uv run ./manage.py runserver       # defaults to config.settings.local (see manage.py)
uv run ./manage.py migrate
uv run ./manage.py shell           # then: exec(open("imports.py").read()) for a preloaded shell

uv run pytest                      # pytest.ini forces --ds=config.settings.test
uv run pytest nnr/users/tests/test_auth.py::test_login_with_email_succeeds   # single test
uv run coverage run -m pytest && uv run coverage html

uv run --group build scripts/build_assets.py           # sass + js -> nnr/static/output
uv run --group build scripts/build_assets.py --check   # is the committed output current?
```

**Running the tests needs a Postgres role with `CREATEDB`**, because the runner creates and
drops `test_nnr_db`. The app role (`DB_USER` in `.env`) does not have it. Either grant it
(`ALTER ROLE nnr_db_user CREATEDB;`) or point the suite at a privileged role without touching
`.env`:

```bash
TEST_DB_USER=<superuser> TEST_DB_HOST= TEST_DB_PASSWORD= uv run pytest
```

`TEST_DB_HOST=` (empty) selects the unix socket, which is what local peer auth needs.

Frontend sources are `nnr/static/input/{sass,js}`; **build output in `nnr/static/output` is what
Django serves** (`STATICFILES_DIRS`) and is committed. Editing files under `output/` directly gets
overwritten by the next build. There is no npm toolchain — `scripts/build_assets.py` uses
libsass/rcssmin/rjsmin from the `build` dependency group.

Python is formatted with `black`. No linter is wired into CI.

## Settings layout

`config/settings/{base,local,production,test}.py`. `local.py` and `production.py` both define
`DATABASES` from the same `.env` keys, so pointing local at prod data is a matter of which
`DB_HOST` is exported — be careful. Notable differences:

- **local**: `DEBUG=True`, media on local disk, email via Amazon SES (anymail) anyway.
- **production**: `django-storages` S3 backends defined *inside* `production.py`
  (`StaticRootS3Boto3Storage` / `MediaRootS3Boto3Storage`) and wired up through the `STORAGES`
  dict, served through CloudFront. It also hardcodes a log file at `logs/debug.log`, so that
  directory must exist or importing the settings raises.
- **test**: defines its own `DATABASES` (`base.py` deliberately has none), locmem cache and
  email, MD5 password hasher, and dummy Stripe keys so no test can reach the live account.

## Apps and how they fit together

| App | Role |
|---|---|
| `recipes/` | `Recipe`, `Tag`, `UserTag`, `RecipeRating`, `RecipePhoto`; the public site |
| `main/` | `Profile` (subscription state) and `PaymentPlan`; all Stripe checkout/webhook handling |
| `comments/` | JSON endpoints for per-recipe comments and flags |
| `nnr/users/` | custom `User` (`AUTH_USER_MODEL = "users.User"`), allauth adapters |
| `nnr/` | project package: templates, static, `custom_storages.py` |
| `config/` | settings, root urlconf, wsgi |

`mixins.py`, `decorators.py` and `imports.py` sit at the **repo root**, not inside an app, and are
imported as top-level modules (`from mixins import ValidUserMixin`). `conftest.py` is at the root
too, and has to be: three of the four apps live there, so a conftest under `nnr/` would not be
visible to them.

### Tests

`pytest.ini` sets `python_files = tests.py test_*.py *_tests.py` — without the `tests.py` entry
pytest silently skips the Django-convention files in `recipes/`, `main/` and `comments/`.
`recipes/tests.py` holds the access-control matrix that checks every gated route against every
subscription state; it is the main guard on the gating described below.

### Subscription gating

Access control is not just `login_required`. Every paid view uses `ValidUserMixin` (root
`mixins.py`) or, for JSON endpoints, `@user_is_valid_api` / `@user_is_paying_api` (root
`decorators.py`). Both read `request.user.profile.subscription_status`, a string mirroring Stripe's
subscription statuses plus the local values `admin` and `free`. `ValidUserMixin.handle_no_permission`
redirects to `main:payment`, `main:processing` or `main:expired` depending on that status — so a
view that forgets the mixin silently becomes free.

Posting endpoints additionally use `RateLimitMixin` / `@rate_limited_api`, which call
`Profile.rate_limit_exceeded()` and return HTTP 429.

`Profile` is created by a `post_save` signal on `User` (`main/signals.py`): staff and
"friends & family" (`user.is_ff`) get a 1000-year subscription, everyone else a 30-day trial.

### Caching

Redis, `KEY_PREFIX = "nnr"`. Two patterns worth knowing:

- `RecipeDetail` caches the whole `Recipe` object under `make_detail_key(slug)` for 24h;
  `Recipe.save()` and `Recipe.delete()` invalidate it. Any code path that mutates a recipe
  *without* going through those methods (bulk updates, raw SQL) leaves a stale page.
- The recipe-of-the-day homepage fragment is a template fragment cache keyed `rotd`, deleted by
  the `choose_rotd` management command via `make_template_fragment_key`.

### Search

Postgres full-text: `Recipe.search_vector` (`SearchVectorField`) plus weighted `SearchVector` /
`SearchRank` built ad hoc in `recipes.views.SearchRecipes` (title weight A, ingredients and
instructions weight B).

### Photos

`RecipePhoto.photo` uses `IMAGE_STORAGE`, which is `default_storage` when `DEBUG` else
`RawMediaStorage` — user uploads land in a *separate raw* bucket (`RAW_MEDIA_BUCKET`) so they can be
optimized before being served from the public bucket. Derivatives are addressed by convention, not
stored: `replace_filename()` swaps the final path segment for `thumbnail.jpeg`, `1200.webp`, etc.,
so the Go optimizer's output filenames and `SCREEN_SIZES`/`PHOTO_EXTENSIONS` in `recipes/models.py`
must stay in sync.

In production the resize is an S3-triggered Lambda. In development, `recipes/signals.py` shells out
to the same Go binary at the hardcoded path
`/usr/local/src/nnr/awslambda/photos/build/photos` (built by `make build` in that submodule).

## awslambda/

One Go tree, not part of the Python build:

- `awslambda/photos/` — **git submodule** (`github.com/ggetzie/nnr-photos`); pure-Go image
  optimizer plus a `cleanup/` module. It has its own `CLAUDE.md` and `Makefile` — read those before
  touching it. Clone with `--recurse-submodules`.

There was also an `awslambda/rotd/` Go lambda that picked the recipe of the day. It was redundant —
`choose_rotd` does the same `featured`/`last_featured` updates in Python — and has been removed.
**Recipe-of-the-day selection lives entirely in `recipes/management/commands/choose_rotd.py`**, run
from cron via `recipes/management/rotd.sh` at 12:00 UTC daily. That command also busts the cached
`rotd` template fragment and posts the tweet.

## Deployment

No CI. Deployment is manual on the server:

```bash
git pull
uv sync --frozen          # required: gunicorn is now run from .venv/, not a system virtualenv
uv run ./manage.py migrate
uv run ./manage.py collectstatic --noinput
sudo supervisorctl restart nnr
```

**`UV_PYTHON_INSTALL_DIR=/opt/uv/python` must be set on the server** (it is in
`/etc/profile.d/uv.sh`). uv otherwise installs Python under the deploying user's home,
and `.venv/bin/python` symlinks there -- which `nnr_user` cannot traverse, so gunicorn
fails with `bad interpreter: Permission denied`. `gunicorn_start.bash` preflights this
and exits with an explanatory message rather than that error. Changing the location
needs `rm -rf .venv` before re-syncing; the interpreter path is baked in at venv
creation.

`srv/{local,production}/` hold the nginx, supervisor and `gunicorn_start.bash` configs, symlinked
into place by the `link_srv` script from [ggetzie/homebin](https://github.com/ggetzie/homebin);
README.md documents the full first-time server setup. `gunicorn_start.bash` execs
`/usr/local/src/nnr/.venv/bin/gunicorn` directly rather than going through `uv run`, so supervisor
does not depend on uv being on its PATH — but that means `uv sync --frozen` must run first.
