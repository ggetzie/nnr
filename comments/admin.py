from django.contrib import admin
from comments.models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = ["short_text", "user_name", "timestamp", "spam"]
    list_editable = ["spam"]
    exclude = ["html"]
    ordering  = ["-timestamp"]

    def short_text(self, obj):
        return obj.text[:20]
    short_text.short_description="Text"
    
    def user_name(self, obj):
        return obj.user.username
    user_name.short_description = "Username"
