from django.contrib import admin

from main.models import Profile, PaymentPlan


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user"]
    readonly_fields = ["stripe_id", "checkout_session", "user"]
    exclude = ["saved_recipes"]


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ["name"]
    readonly_fields = ["name_slug"]
