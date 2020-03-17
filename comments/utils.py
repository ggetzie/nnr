import random
import string 

from django.contrib.auth import get_user_model

from comments.models import Comment
from recipes.models import Recipe

User = get_user_model()

def random_comment(recipe):
    length = random.randint(50, 1000)
    text = "".join([random.choice(string.printable) for _ in range(length)])
    user = random.choice(User.objects.filter(is_staff=False,
                                             profile__payment_status=3))
    comment = Comment(recipe=recipe,
                      user=user,
                      text=text)
    comment.save()

