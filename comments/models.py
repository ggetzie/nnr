import datetime
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

import markdown

from recipes.models import Recipe

def utc_now():
    return datetime.datetime.now(tz=datetime.timezone.utc)

EPOCH_START = datetime.datetime(year=1970, 
                                month=1, 
                                day=1, 
                                tzinfo=datetime.timezone.utc)

class Comment(models.Model):
    id = models.UUIDField(_("id"), 
                          primary_key=True, 
                          editable=False,
                          default=uuid.uuid4)
    text = models.TextField(_("Comment"))
    html = models.TextField(_("Comment HTML"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True)
    nesting = models.PositiveSmallIntegerField(_("Nesting"), default=0)
    deleted = models.BooleanField(_("Deleted"), default=False)
    timestamp = models.DateTimeField(_("Timestamp"), default=utc_now)
    last_edited = models.DateTimeField(_("Last Edited"), 
                                       default=EPOCH_START)
    spam = models.BooleanField(_("Marked Spam"), default=False)
    flag_count = models.IntegerField(_("Flag Count"), default=0)

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
        self.text = "*comment deleted*"
        self.save()

class Flag(models.Model):
    id = models.UUIDField(_("id"), 
                          primary_key=True, 
                          editable=False,
                          default=uuid.uuid4)
    comment = models.ForeignKey(Comment, 
                                on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.CASCADE)
    timestamp = models.DateTimeField(_("timestamp"),
                                     default=utc_now)

    class Meta:
        ordering = ["-timestamp"]
        constraints = [models.UniqueConstraint(fields=["comment", "user"],
                                               name="unique_comment_flag")]