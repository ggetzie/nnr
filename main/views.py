from allauth.account.utils import complete_signup
from crispy_forms.layout import Submit
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.search import (SearchQuery, 
                                            SearchRank, 
                                            SearchVector)
from django.core.exceptions import PermissionDenied
from django.db.models import Avg
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (CreateView, UpdateView, DeleteView, ListView,
                                  DetailView, FormView)
from main.forms import (CreateRecipeForm, UpdateRecipeForm, TagRecipeForm,
                        SaveRecipeForm, RateRecipeForm, RecipeSearchForm,
                        NNRSignupForm)

from main.models import (Recipe, RecipeRating, Profile, Tag, UserTag, 
                         LetterCount)

from main.payments import (handle_payment_success, handle_payment_action,
                           handle_payment_failure)

from main.utils import (get_trial_end, get_subscription_plan)

import datetime
import logging
import json
import stripe

User = get_user_model()                        
logger = logging.getLogger(__name__)

class ValidUserMixin(UserPassesTestMixin):
    payment_failed_message = ("We were unable to process your last payment. "
                              "Please update your payment information to proceed")

    payment_confirm_message = ("Your payment method requires additional confirmation "
                               "Please check your email and complete the required "
                               "confirmation steps to proceed")

    def test_func(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        if self.request.user.profile.payment_status in (2, 3):
            return True
        if self.request.user.profile.payment_status == 0:
            # payment failed
            self.permission_denied_message = self.payment_failed_message
            return False
        if self.request.user.profile.payment_status == 1:
            # payment needs confirmation
            self.permission_denied_message = self.payment_confirm_message
            return False

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if self.request.user.profile.payment_status == 0:
                messages.error(self.request, self.payment_failed_message)
                return redirect("users:update_payment", 
                                username=self.request.user.username)
            if self.request.user.profile.payment_status == 1:
                messages.warning(self.request, self.payment_confirm_message)
                return redirect("users:confirm_payment", 
                                username=self.request.user.username)
        return super().handle_no_permission()

def nnr_signup(request):
    if request.is_ajax():
        logger.info(f"AJAX Request: {request.body}")
        data = json.loads(request.body)
        payment_method = data.pop("payment_method")
        logger.info(f"Got payment method: {payment_method}")
        form_data = {k:v for k, v in data.items() 
                              if k in NNRSignupForm.base_fields}
        # Password fields don't appear in NNRSignupForm.base_fields
        # Add them manually                              
        form_data["password1"] = data["password1"]
        form_data["password2"] = data["password2"]
        logger.info(f"Creating form with data: {form_data}")                            
        form = NNRSignupForm(form_data)
        if form.is_valid():
            user = form.save(request)
            # Create a customer and subscription with stripe
            stripe.api_key = settings.STRIPE_SK
            customer = stripe.Customer.create(
                payment_method=payment_method,
                email=user.email,
                invoice_settings={
                    "default_payment_method":payment_method
                }
            )
            profile = Profile.objects.get(user=user)
            profile.stripe_id = customer.id
            profile.save()
            logger.info(f"created customer: {customer.id}")
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {
                        "plan": get_subscription_plan()
                    }
                ],
                trial_end=get_trial_end(),
                expand=["latest_invoice.payment_intent"]
            )
            logger.info(f"created subscription: {subscription}")
            success_url = reverse_lazy("thankyou")
            email_verification = settings.ACCOUNT_EMAIL_VERIFICATION
            response = complete_signup(request, user, 
                                       email_verification=email_verification,
                                       success_url = success_url)
            return JsonResponse(subscription, safe=False)
        else:
            logger.info(f"Form invalid. Errors: {form.errors}")
            return JsonResponse(form.errors)

    else:
        form = NNRSignupForm()
    return render(request, "account/signup.html", 
                           context={"form": form})

def update_payment(request, username):
    user = User.objects.get(username=username)
    if request.is_ajax():
        data = json.loads(request.body)
        token = data["token"]
        stripe.api_key = settings.STRIPE_SK
        if not user.profile.stripe_id:
            errmsg = "User has no customer id"
            return JsonResponse({"status": "error",
                                 "error" : {"message": errmsg}})
        stripe.Customer.modify(user.profile.stripe_id,
                               source=token)
        return JsonResponse({"status": "success"})

        
    return render(request, "users/update_payment.html", 
                  context={"user": user})

def public_key(request):
    if request.is_ajax():
        return JsonResponse({"publicKey": settings.STRIPE_PK})
    else:
        return HttpResponseBadRequest("<h1>Bad Request</h1>")

@csrf_exempt
def webhook(request):
    payload = request.body
    event = None
    stripe.api_key = settings.STRIPE_SK
    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError:
        logger.info(f"Could not parse event")
        return HttpResponse(status=400)

    logger.info(f"received event - {event.type}")        

    if event.type == "invoice.payment_succeeded":
        handle_payment_success(event)
    elif event.type == "invoice.payment_action_required":
        handle_payment_action(event)
    elif event.type == "invoice.payment_failed":
        handle_payment_failure(event)
    else:
        logger.info(f"Received unhandled event: {event.type}")

    return HttpResponse(status=200)


class CreateRecipe(ValidUserMixin, CreateView):
    model = Recipe
    form_class = CreateRecipeForm
    
    def get_initial(self):
        initial = super().get_initial()
        initial["user"] = self.request.user
        return initial


class RecipeDetail(ValidUserMixin, DetailView):
    model = Recipe
    slug_field = "title_slug"
    context_object_name = "recipe"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usertags"] = UserTag.objects.filter(user=self.request.user,
                                                     recipe=self.object)
        context["tagform"] = TagRecipeForm(initial={"user": self.request.user,
                                                    "recipe": self.object})
        saveform = SaveRecipeForm(initial={"user": self.request.user,
                                           "recipe": self.object})                                                        
        if self.object in self.request.user.profile.saved_recipes.all():
            btn = "Unsave"
            css = "btn btn-outline-primary btn-sm"
        else:
            btn = "Save"
            css = "btn btn-primary btn-sm"
        submit = Submit(btn, btn)
        submit.field_classes=css
        saveform.helper.add_input(submit)
        context["saveform"] = saveform

        rate_initial = {"user": self.request.user,
                        "recipe": self.object}
        try:
            rr = RecipeRating.objects.get(recipe=self.object,
                                              profile=self.request.user.profile)
            rate_initial["rating"] = rr.rating
        except RecipeRating.DoesNotExist:
            pass

        context["rateform"] = RateRecipeForm(initial=rate_initial)
        context["average_rating"] = RecipeRating.objects.\
                                    filter(recipe=self.object).\
                                    aggregate(Avg("rating"))["rating__avg"]
        return context


class RecipeOfTheDay(DetailView):
    model = Recipe
    context_object_name = "recipe"
    template_name = "main/rotd.html"

    def get_object(self, queryset=None):
        return Recipe.objects.get(featured=True)


class RecipeList(ValidUserMixin, ListView):
    model = Recipe
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lettercounts"] = LetterCount.objects.all()
        context["title"] = "All Recipes"
        return context


class UpdateRecipe(UserPassesTestMixin, UpdateView):
    model = Recipe
    form_class = UpdateRecipeForm
    slug_field = "title_slug"

    def test_func(self):
        self.object = self.get_object()
        return (self.request.user.is_staff or 
                self.request.user == self.object.user)


class DeleteRecipe(UserPassesTestMixin, DeleteView):
    model = Recipe
    success_url = reverse_lazy("main:recipe_list")
    slug_field = "title_slug"

    def test_func(self):
        self.object = self.get_object()
        return (self.request.user.is_staff or
                self.request.user == self.object.user)


class TagList(ValidUserMixin, ListView):
    model = Tag
    paginate_by = 144


class TagDetail(ValidUserMixin, ListView):
    model = Recipe
    slug_field = "name_slug"
    paginate_by = 25
    template_name = "main/tag_detail.html"

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, name_slug=self.kwargs["slug"])
        qs = self.tag.recipe_set.all()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        return context
    


class TagRecipe(ValidUserMixin, FormView):
    form_class = TagRecipeForm

    def form_valid(self, form):
        form.save_tags()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("main:recipe_detail", kwargs=kw))


class SaveRecipe(ValidUserMixin, FormView):
    form_class = SaveRecipeForm

    def form_valid(self, form):
        if not self.request.user == form.cleaned_data["user"]:
            raise PermissionDenied        
        form.save_recipe()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect(reverse_lazy("main:recipe_detail", kwargs=kw))


class RateRecipe(ValidUserMixin, FormView):
    form_class = RateRecipeForm

    def form_valid(self, form):
        if not self.request.user == form.cleaned_data["user"]:
            raise PermissionDenied
        form.rate_recipe()
        kw = {"slug": form.cleaned_data["recipe"].title_slug}
        return redirect (reverse_lazy("main:recipe_detail", kwargs=kw))


class SavedRecipeList(UserPassesTestMixin, ListView):
    model = Recipe
    template_name = "users/saved_recipes.html"
    paginate_by = 25

    def test_func(self):
        return (self.request.user.is_staff or
                self.request.user.username == self.kwargs["username"])

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        qs = self.user.profile.saved_recipes.all()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


class SubmittedRecipeList(ValidUserMixin, ListView):
    model = Recipe
    template_name = "users/submitted_recipes.html"
    paginate_by = 25

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        qs = Recipe.objects.filter(user=self.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


class RatedRecipeList(UserPassesTestMixin, ListView):
    model = RecipeRating
    template_name = "users/rated_recipes.html"
    paginate_by = 25

    def test_func(self):
        return (self.request.user.is_staff or 
                self.request.user.username == self.kwargs["username"])

    def get_queryset(self):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        ratings = (RecipeRating.objects
                   .filter(profile=self.user.profile)
                   .order_by("-rating", "recipe__sort_title"))
        return ratings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.user
        return context


class RecipeByLetterList(ValidUserMixin, ListView):
    model = Recipe
    paginate_by = 25

    def get_queryset(self):
        qs = Recipe.objects.filter(first_letter=self.kwargs["first_letter"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f'"{self.kwargs["first_letter"]}" Recipes'
        context["lettercounts"] = LetterCount.objects.all()
        context["current"] = self.kwargs["first_letter"]
        return context
        

class SearchRecipes(ValidUserMixin, FormView):
    form_class = RecipeSearchForm
    template_name = "main/search.html"
    success_url = reverse_lazy("main:search_recipes")

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        terms = self.request.GET.get("terms", None)
        if terms:
            title_vector = SearchVector("title", weight="A")
            ingredients_vector = SearchVector("ingredients_text", weight="B")
            instructions_vector = SearchVector("instructions_text", weight="B")
            vector = title_vector + ingredients_vector + instructions_vector

            query = SearchQuery(terms)
            results = (Recipe.objects
                      .annotate(search=vector).filter(search=terms)
                      .annotate(rank=SearchRank(vector, query))
                      .order_by("-rank"))
            context["results"] = results
            context["terms"] = terms
        return context