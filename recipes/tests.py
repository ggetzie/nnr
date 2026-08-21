"""Access-control and caching smoke tests.

The point of this module is to pin down *who can reach what* before the
Django/allauth/crispy upgrade, because subscription gating here is not enforced by
`login_required` but by `ValidUserMixin` (root ``mixins.py``) and the API decorators
in root ``decorators.py``. A view that loses its mixin during a refactor becomes
silently free to the world, and nothing else in the suite would notice.

Each gated route is checked against every subscription state, so the redirect
targets in ``ValidUserMixin.handle_no_permission`` are covered too.
"""

import pytest
from django.core.cache import cache
from django.urls import reverse

from recipes.models import LetterCount, Recipe, make_detail_key

pytestmark = pytest.mark.django_db


def build(name, kwargs_fn, ctx):
    return reverse(name, kwargs=kwargs_fn(ctx))


NO_KWARGS = lambda ctx: {}  # noqa: E731

# Reachable without an account at all.
PUBLIC_GET = [
    ("home", NO_KWARGS),
    ("about", NO_KWARGS),
    ("privacy", NO_KWARGS),
    ("support", NO_KWARGS),
    ("tos", NO_KWARGS),
    ("recipes:recipe_list", NO_KWARGS),
    ("recipes:tag_list", NO_KWARGS),
    ("recipes:recipe_detail", lambda ctx: {"slug": ctx["recipe"].title_slug}),
    ("recipes:tag_detail", lambda ctx: {"slug": ctx["tag"].name_slug}),
    ("recipes:letter_recipe", lambda ctx: {"first_letter": "T"}),
]

# Require an active/trialing subscription (or staff).
GATED_GET = [
    ("recipes:home", NO_KWARGS),
    ("recipes:recipe_create", NO_KWARGS),
    ("recipes:search_recipes", NO_KWARGS),
    ("users:user_tags", lambda ctx: {"username": ctx["username"]}),
]


def ids(table):
    return [name for name, _ in table]


@pytest.fixture
def ctx(recipe, tag, subscribed_user):
    return {
        "recipe": recipe,
        "tag": tag,
        "username": subscribed_user.username,
    }


# --------------------------------------------------------------------------
# Public pages
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name,kwargs_fn", PUBLIC_GET, ids=ids(PUBLIC_GET))
def test_public_pages_reachable_anonymously(anon_client, ctx, name, kwargs_fn):
    assert anon_client.get(build(name, kwargs_fn, ctx)).status_code == 200


# --------------------------------------------------------------------------
# Gated pages, one case per subscription state
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name,kwargs_fn", GATED_GET, ids=ids(GATED_GET))
def test_gated_pages_reject_anonymous(anon_client, ctx, name, kwargs_fn):
    response = anon_client.get(build(name, kwargs_fn, ctx))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.parametrize("name,kwargs_fn", GATED_GET, ids=ids(GATED_GET))
def test_gated_pages_allow_trial(trial_client, ctx, name, kwargs_fn):
    assert trial_client.get(build(name, kwargs_fn, ctx)).status_code == 200


@pytest.mark.parametrize("name,kwargs_fn", GATED_GET, ids=ids(GATED_GET))
def test_gated_pages_allow_subscriber(subscribed_client, ctx, name, kwargs_fn):
    assert subscribed_client.get(build(name, kwargs_fn, ctx)).status_code == 200


@pytest.mark.parametrize("name,kwargs_fn", GATED_GET, ids=ids(GATED_GET))
def test_gated_pages_allow_staff(staff_client, ctx, name, kwargs_fn):
    assert staff_client.get(build(name, kwargs_fn, ctx)).status_code == 200


@pytest.mark.parametrize("name,kwargs_fn", GATED_GET, ids=ids(GATED_GET))
def test_gated_pages_send_lapsed_to_payment(lapsed_client, ctx, name, kwargs_fn):
    response = lapsed_client.get(build(name, kwargs_fn, ctx))
    assert response.status_code == 302
    assert response.url == reverse("main:payment")


@pytest.mark.parametrize("name,kwargs_fn", GATED_GET, ids=ids(GATED_GET))
def test_gated_pages_send_pending_to_processing(pending_client, ctx, name, kwargs_fn):
    response = pending_client.get(build(name, kwargs_fn, ctx))
    assert response.status_code == 302
    assert response.url == reverse("main:processing")


@pytest.mark.parametrize("name,kwargs_fn", GATED_GET, ids=ids(GATED_GET))
def test_gated_pages_send_canceled_to_expired(canceled_client, ctx, name, kwargs_fn):
    response = canceled_client.get(build(name, kwargs_fn, ctx))
    assert response.status_code == 302
    assert response.url == reverse("main:expired")


# --------------------------------------------------------------------------
# JSON endpoints guarded by decorators rather than the mixin
# --------------------------------------------------------------------------


def test_all_tags_rejects_anonymous(anon_client):
    response = anon_client.get(reverse("recipes:get_all_tags"))
    assert response.status_code == 200
    assert "error" in response.json()


def test_all_tags_rejects_lapsed(lapsed_client):
    assert "error" in lapsed_client.get(reverse("recipes:get_all_tags")).json()


def test_all_tags_allows_subscriber(subscribed_client, user_tag):
    payload = subscribed_client.get(reverse("recipes:get_all_tags")).json()
    assert payload["tag_list"] == ["Breakfast"]


# --------------------------------------------------------------------------
# POST-only endpoints (these FormViews define no template, so GET is not valid)
# --------------------------------------------------------------------------


def test_save_recipe_stores_against_profile(subscribed_client, subscribed_user, recipe):
    response = subscribed_client.post(
        reverse("recipes:save_recipe"),
        {"user": subscribed_user.id, "recipe": recipe.id},
    )
    assert response.status_code == 302
    assert recipe in subscribed_user.profile.saved_recipes.all()


def test_rate_recipe_records_rating(subscribed_client, subscribed_user, recipe):
    response = subscribed_client.post(
        reverse("recipes:rate_recipe"),
        {"user": subscribed_user.id, "recipe": recipe.id, "rating": 4},
    )
    assert response.status_code == 302
    assert recipe.reciperating_set.get(user=subscribed_user).rating == 4


def test_untag_requires_post(subscribed_client):
    assert subscribed_client.get(reverse("recipes:untag")).status_code == 405


# --------------------------------------------------------------------------
# Cache invalidation. RecipeDetail caches the whole object for 24h and only
# Recipe.save()/delete() clear it, so this invariant is easy to break silently.
# --------------------------------------------------------------------------


def test_recipe_detail_populates_cache(anon_client, recipe):
    cache.clear()
    key = make_detail_key(recipe.title_slug)
    assert cache.get(key) is None

    anon_client.get(recipe.get_absolute_url())
    assert cache.get(key) is not None


def test_recipe_save_invalidates_cache(anon_client, recipe):
    cache.clear()
    key = make_detail_key(recipe.title_slug)
    anon_client.get(recipe.get_absolute_url())
    assert cache.get(key) is not None

    recipe.instructions_text = "1. Something else"
    recipe.save()
    assert cache.get(key) is None


def test_recipe_delete_invalidates_cache(anon_client, recipe):
    cache.clear()
    key = make_detail_key(recipe.title_slug)
    anon_client.get(recipe.get_absolute_url())
    assert cache.get(key) is not None

    recipe.delete()
    assert cache.get(key) is None


# --------------------------------------------------------------------------
# Model behaviour relied on by the views above
# --------------------------------------------------------------------------


def test_save_derives_slug_and_sort_fields():
    recipe = Recipe.objects.create(
        title="The Best Blueberry Muffins",
        ingredients_text="- blueberries",
        instructions_text="1. Bake",
    )
    assert recipe.title_slug == "the-best-blueberry-muffins"
    # "the" and "best" are stopwords, so sorting starts at "blueberry"
    assert recipe.first_letter == "B"
    assert recipe.sort_title == "blueberry-muffins"


def test_save_maintains_letter_counts():
    Recipe.objects.create(
        title="Waffles",
        ingredients_text="- flour",
        instructions_text="1. Cook",
    )
    assert LetterCount.objects.get(letter="W").quantity == 1


def test_markdown_is_rendered_on_save(recipe):
    assert "<li>flour</li>" in recipe.ingredients_html
