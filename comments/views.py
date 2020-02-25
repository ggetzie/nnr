import datetime

from django.http import JsonResponse
from django.shortcuts import render

from comments.models import Comment

# users can view comments during trial
# @validuser
def list_comments(request):
    recipe_id = request.GET.get("recipe_id", "")
    before = request.GET.get("before", None)
    max_comments = request.GET.get("max_comments", 100)
    if before:
        before_comment = Comment.objects.get(pk=before)
        get_before = before_comment.timestamp
    else:
        get_before = datetime.datetime.now(tz=datetime.timezone.utc)
    comments = Comment.objects.filter(recipe=recipe_id,
                                      timestamp__lt=get_before,
                                      spam=False,
                                      flag_count__lt=10,
                                      deleted=False
                                     )[:max_comments]
    comment_list = [{"id": c.id,
                     "text": c.text,
                     "html": c.html,
                     "user_id": c.user.id,
                     "parent_id": c.parent,
                     "nesting": c.nesting,
                     "timestamp": c.timestamp,
                     "last_edited": c.last_edited} for c in comments]
    return JsonResponse({"status": "ok",
                        "comment_list": comment_list}) 

# users can only post comments after free trial    
# @payinguser
# @ratelimited
def add_comment(request):
    pass

# @payinguser
# @user_is_owner
def edit_comment(request):
    pass

# @payinguser
# @user_is_owner
def delete_comment(request):
    pass

