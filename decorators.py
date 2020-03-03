# nnr specific decorators
from functools import wraps

from django.http import JsonResponse

ERROR_MSG = "You must have a current subscription to use this feature"

def user_is_valid_api(view_func):
    """
    Verifies that the user is either paying subscriber or on free trial
    for api requests (returns JSON response)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.is_valid():
            return view_func(request, *args, **kwargs)
        return JsonResponse({"error": ERROR_MSG})
    return _wrapped_view
    


def user_is_paying_api(view_func):
    """
    Verifies that the user has paid (payment status success)
    for api requests (returns JSON response)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.paid():
            return view_func(request, *args, **kwargs)
        return JsonResponse({"error": ("This feature is only available"
                                        " after the free trial period.")})
    return _wrapped_view
    


def rate_limited_api(view_func):
    """
    Checks users last post to rate limited endpoints 
    (adding comments or recipes) and rejects if  within timeout period
    for api requests (returns JSON response)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        exceeded, msg = request.user.profile.rate_limit_exceeded()
        if exceeded:
            return JsonResponse({"error": msg})
        else:
            return view_func(request, *args, **kwargs)
    return _wrapped_view
