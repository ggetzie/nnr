"""Comment JSON endpoint tests.

These four views are guarded by the decorators in root ``decorators.py`` rather
than by ``ValidUserMixin``, and they signal failure with a 200 + {"error": ...}
body instead of a status code. That makes an accidental loss of the guard
invisible to any check that only looks at status codes, so assert on the body.
"""

import json

import pytest
from django.urls import reverse

from comments.models import Comment

pytestmark = pytest.mark.django_db


def post_json(client, name, payload):
    return client.post(
        reverse(name), data=json.dumps(payload), content_type="application/json"
    )


@pytest.fixture
def comment(subscribed_user, recipe):
    return Comment.objects.create(
        user=subscribed_user, recipe=recipe, text="Tasted great"
    )


# --------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------


def test_list_rejects_anonymous(anon_client, recipe):
    response = anon_client.get(reverse("comments:list"), {"recipe_id": recipe.id})
    assert "error" in response.json()


def test_list_rejects_lapsed_subscriber(lapsed_client, recipe):
    response = lapsed_client.get(reverse("comments:list"), {"recipe_id": recipe.id})
    assert "error" in response.json()


def test_list_returns_comments_for_subscriber(subscribed_client, recipe, comment):
    response = subscribed_client.get(
        reverse("comments:list"), {"recipe_id": recipe.id}
    )
    payload = response.json()
    assert payload["status"] == "ok"
    assert [c["text"] for c in payload["comment_list"]] == ["Tasted great"]


def test_list_excludes_deleted_and_spam(subscribed_client, recipe, comment):
    comment.soft_delete()
    response = subscribed_client.get(
        reverse("comments:list"), {"recipe_id": recipe.id}
    )
    assert response.json()["comment_list"] == []


# --------------------------------------------------------------------------
# add
# --------------------------------------------------------------------------


def test_add_requires_post(subscribed_client):
    assert subscribed_client.get(reverse("comments:add")).status_code == 405


def test_add_rejects_anonymous(anon_client, recipe, subscribed_user):
    response = post_json(
        anon_client,
        "comments:add",
        {"user": subscribed_user.id, "recipe": recipe.id, "text": "hi"},
    )
    assert "error" in response.json()
    assert Comment.objects.count() == 0


def test_add_creates_comment_and_renders_markdown(
    subscribed_client, recipe, subscribed_user
):
    response = post_json(
        subscribed_client,
        "comments:add",
        {"user": subscribed_user.id, "recipe": recipe.id, "text": "**tasty**"},
    )
    assert response.json()["comment"]["text"] == "**tasty**"
    assert "<strong>tasty</strong>" in Comment.objects.get().html


def test_add_is_rate_limited(subscribed_client, recipe, subscribed_user):
    body = {"user": subscribed_user.id, "recipe": recipe.id, "text": "first"}
    assert "error" not in post_json(subscribed_client, "comments:add", body).json()

    second = post_json(subscribed_client, "comments:add", body).json()
    assert "error" in second
    assert Comment.objects.count() == 1


# --------------------------------------------------------------------------
# edit / delete
# --------------------------------------------------------------------------


def test_edit_updates_own_comment(subscribed_client, comment):
    response = post_json(
        subscribed_client, "comments:edit", {"id": str(comment.id), "text": "edited"}
    )
    assert response.json()["status"] == "ok"
    comment.refresh_from_db()
    assert comment.text == "edited"
    assert comment.has_been_edited()


def test_edit_rejects_other_users_comment(trial_client, comment):
    response = post_json(
        trial_client, "comments:edit", {"id": str(comment.id), "text": "hijacked"}
    )
    assert "error" in response.json()
    comment.refresh_from_db()
    assert comment.text == "Tasted great"


def test_delete_soft_deletes_own_comment(subscribed_client, comment):
    response = post_json(
        subscribed_client, "comments:delete", {"id": str(comment.id)}
    )
    assert response.json()["status"] == "ok"
    comment.refresh_from_db()
    assert comment.deleted is True


def test_delete_rejects_other_users_comment(trial_client, comment):
    response = post_json(trial_client, "comments:delete", {"id": str(comment.id)})
    assert "error" in response.json()
    comment.refresh_from_db()
    assert comment.deleted is False
