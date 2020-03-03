import datetime
import json
import logging

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from comments.models import Comment
from decorators import (user_is_paying_api, user_is_valid_api, 
                        rate_limited_api)
from recipes.models import Recipe

User = get_user_model()

logger = logging.getLogger(__name__)

# users can view comments during trial
@user_is_valid_api
def list_comments(request):
    recipe_id = request.GET.get("recipe_id", "")
    start_from = request.GET.get("start_from", None)
    max_comments = request.GET.get("max_comments", 100)
    if start_from:
        before_comment = Comment.objects.get(pk=start_from)
        get_before = before_comment.timestamp
    else:
        get_before = datetime.datetime.now(tz=datetime.timezone.utc)
    comments = Comment.objects.filter(recipe=recipe_id,
                                      timestamp__lt=get_before,
                                      spam=False,
                                      flag_count__lt=10,
                                      deleted=False
                                     )[:max_comments]
    comment_list = [c.json() for c in comments]
    return JsonResponse({"status": "ok",
                        "comment_list": comment_list}) 

# users can only post comments after free trial    
# @payinguser
# @ratelimited
@require_POST
@user_is_paying_api
@rate_limited_api
def add_comment(request):
    data = json.loads(request.body)
    user = User.objects.get(id=data["user"])
    recipe = Recipe.objects.get(id=data["recipe"])
    comment = Comment(user=user,
                      recipe=recipe,
                      text=data["text"])
    comment.save()
    response_data = {
        "comment": comment.json()
    }
    return JsonResponse(data=response_data)

@user_is_paying_api
def edit_comment(request):
    data = json.loads(request.body)
    comment = Comment.objects.get(id=data["id"])
    if request.user != comment.user:
        return JsonResponse({"error": ("You do not have permission "
                                       "to edit this comment")})
    comment.text = data["text"]
    comment.save()
    return JsonResponse({"status": "ok",
                         "message": "Comment updated",
                         "comment": comment.json()})

@user_is_paying_api
def delete_comment(request):
    data = json.loads(request.body)
    comment = Comment.objects.get(id=data["id"])
    if request.user != comment.user:
        return JsonResponse({"error": ("You do not have permission to "
                                       "delete this comment.")})
    comment.soft_delete()
    return JsonResponse({"status": "ok",
                         "message": "Comment deleted"})

