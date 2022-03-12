import datetime
import uuid

from django.conf import settings
from django.db import models

import markdown
from dateutil.relativedelta import relativedelta

from recipes.models import Recipe


def utc_now():
    return datetime.datetime.now(tz=datetime.timezone.utc)


EPOCH_START = datetime.datetime(year=1970, month=1, day=1, tzinfo=datetime.timezone.utc)


class Comment(models.Model):
    id = models.UUIDField("id", primary_key=True, editable=False, default=uuid.uuid4)
    text = models.TextField("Comment")
    html = models.TextField("Comment HTML")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True)
    nesting = models.PositiveSmallIntegerField("Nesting", default=0)
    deleted = models.BooleanField("Deleted", default=False)
    timestamp = models.DateTimeField("Timestamp", default=utc_now)
    last_edited = models.DateTimeField("Last Edited", default=EPOCH_START)
    spam = models.BooleanField("Marked Spam", default=False)
    flag_count = models.IntegerField("Flag Count", default=0)

    class Meta:
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        if self.id:
            self.last_edited = utc_now()
        self.html = markdown.markdown(self.text)
        return super().save(*args, **kwargs)

    def has_been_edited(self):
        return self.last_edited > EPOCH_START

    def soft_delete(self):
        self.deleted = True
        self.save()

    def time_ago(self):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        elapsed = relativedelta(now, self.timestamp)
        if elapsed.years > 0:
            unit = f"year{'s' if elapsed.years > 1 else ''}"
            val = elapsed.years * -1
        elif elapsed.months > 0:
            unit = f"month{'s' if elapsed.months > 1 else ''}"
            val = elapsed.months
        elif elapsed.weeks > 0:
            unit = f"week{'s' if elapsed.weeks > 1 else ''}"
            unit = "week" if elapsed.weeks == 1 else "weeks"
            val = elapsed.weeks
        elif elapsed.days > 0:
            unit = f"day{'s' if elapsed.days > 1 else ''}"
            val = elapsed.days
        elif elapsed.hours > 0:
            unit = f"hour{'s' if elapsed.hours > 1 else ''}"
            val = elapsed.hours
        elif elapsed.minutes > 0:
            unit = f"minute{'s' if elapsed.minutes > 1 else ''}"
            val = elapsed.minutes
        elif elapsed.seconds > 0:
            unit = f"second{'s' if elapsed.seconds > 1 else ''}"
            val = elapsed.seconds
        else:
            unit = "seconds"
            val = 0

        return f"{val} {unit} ago"

    def json(self):
        # return dict for use in json response
        return {
            "id": self.id,
            "user": {
                "id": self.user.id,
                "username": self.user.username,
            },
            "html": self.html,
            "text": self.text,
            "timestamp": self.time_ago(),
            "edited": self.has_been_edited(),
            "parent": self.parent,
            "nesting": self.nesting,
        }


class Flag(models.Model):
    id = models.UUIDField("id", primary_key=True, editable=False, default=uuid.uuid4)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField("timestamp", default=utc_now)

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"], name="unique_comment_flag"
            )
        ]
