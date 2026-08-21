# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`nnr` is the Django site behind [nononsense.recipes](https://nononsense.recipes) — an ad-free,
subscription (Stripe) recipe site, generated originally from Cookiecutter Django. Postgres +
Redis + gunicorn/nginx/supervisor on a single Ubuntu host (AWS Lightsail); media and static
files go to S3/CloudFront in production. Two Go AWS Lambdas live under `awslambda/`.

## Commands

Scripts and `.vscode/settings.json` assume a virtualenv at `/usr/local/src/env/nnr`
(`source /usr/local/src/env/nnr/bin/activate`). Environment variables come from `.env` in the
repo root, read by `django-environ` at settings import — every `manage.py` invocation needs it.

```bash
./manage.py runserver              # defaults to config.settings.local (see manage.py)
./manage.py migrate
./manage.py shell                  # then: exec(open("imports.py").read()) for a preloaded shell

pytest                             # pytest.ini forces --ds=config.settings.test
pytest nnr/users/tests/test_views.py::TestUserUpdateView::test_get_success_url   # single test
coverage run -m pytest && coverage html    # .coveragerc includes only nnr/*

npm run build                      # gulp generate-assets: sass + js -> nnr/static/output
npm run dev                        # gulp: runserver + browser-sync (proxy localhost:8000) + watch
```

Frontend sources are `nnr/static/input/{sass,js}`; **build output in `nnr/static/output` is what
Django serves** (`STATICFILES_DIRS`) and is committed. Editing files under `output/` directly gets
overwritten by the next gulp run.

Lint config exists (`.pylintrc` with `pylint_django`, flake8/mypy in `setup.cfg`) but is not wired
into CI. Python is formatted with `black`.

## Settings layout

`config/settings/{base,local,production,test}.py`. `local.py` and `production.py` both define
`DATABASES` from the same `.env` keys, so pointing local at prod data is a matter of which
`DB_HOST` is exported — be careful. Notable differences:

- **local**: `DEBUG=True`, media on local disk, email via Amazon SES (anymail) anyway.
- **production**: `django-storages` S3 backends defined *inside* `production.py`
  (`StaticRootS3Boto3Storage` / `MediaRootS3Boto3Storage`), served through CloudFront.
- **test**: locmem cache and email, MD5 password hasher.

## Apps and how they fit together

| App | Role |
|---|---|
| `recipes/` | `Recipe`, `Tag`, `UserTag`, `RecipeRating`, `RecipePhoto`; the public site |
| `main/` | `Profile` (subscription state) and `PaymentPlan`; all Stripe checkout/webhook handling |
| `comments/` | JSON endpoints for per-recipe comments and flags |
| `nnr/users/` | custom `User` (`AUTH_USER_MODEL = "users.User"`), allauth adapters |
| `nnr/` | project package: templates, static, `custom_storages.py`, `conftest.py` |
| `config/` | settings, root urlconf, wsgi |

`mixins.py`, `decorators.py` and `imports.py` sit at the **repo root**, not inside an app, and are
imported as top-level modules (`from mixins import ValidUserMixin`).

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
  *without* going through those methods (bulk updates, raw SQL, the rotd Lambda) leaves a stale page.
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

Two independent Go trees, neither part of the Python build:

- `awslambda/photos/` — **git submodule** (`github.com/ggetzie/nnr-photos`); pure-Go image
  optimizer plus a `cleanup/` module. It has its own `CLAUDE.md` and `Makefile` — read those before
  touching it. Clone with `--recurse-submodules`.
- `awslambda/rotd/` — picks the recipe of the day, writes to Postgres with `pgx`, tweets it.
  Built on the server with `go build -o build/rotd rotd.go`.

The rotd Lambda now owns choosing the featured recipe; the `choose_rotd` Django command runs from
cron (`recipes/management/rotd.sh`, 12:00 UTC daily) mainly to bust the cached fragment.

## Deployment

No CI. Deployment is manual on the server: `git pull`, migrate, `collectstatic`, restart the
supervisor program. `srv/{local,production}/` hold the nginx, supervisor and `gunicorn_start.bash`
configs, symlinked into place by the `link_srv` script from
[ggetzie/homebin](https://github.com/ggetzie/homebin); README.md documents the full first-time
server setup.
