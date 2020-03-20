from allauth.account.utils import complete_signup

from dateutil.relativedelta import relativedelta
import environ

from django.conf import settings
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (CreateView, UpdateView, DeleteView, ListView,
                                  DetailView, FormView)
from main.forms import NNRSignupForm

from main.models import Profile

from main.payments import (handle_payment_success, handle_payment_action,
                           handle_payment_failure, handle_payment_update,
                           update_customer_card, handle_session_complete)

from main.utils import (get_trial_end, get_subscription_plan)

from mixins import ValidUserMixin

import datetime
import logging
import json
import stripe

env = environ.Env()
logger = logging.getLogger(__name__)

DOMAIN_URL = "http://nnr" if settings.DEBUG else "https://nononsense.recipes"

def create_checkout_session(request):
    if request.is_ajax():
        data = json.loads(request.body)
        form_data = {k:v for k, v in data.items() 
                              if k in NNRSignupForm.base_fields}
        # Password fields don't appear in NNRSignupForm.base_fields
        # Add them manually                              
        form_data["password1"] = data["password1"]
        form_data["password2"] = data["password2"]
        form = NNRSignupForm(form_data)
        if form.is_valid():
            user = form.save(request)
            checkout_session = stripe.checkout.Session.create(
                success_url= (DOMAIN_URL + 
                              reverse_lazy("main:checkout_success") + 
                              "?session_id={CHECKOUT_SESSION_ID}"),
                cancel_url=DOMAIN_URL+reverse_lazy("main:checkout_cancel"),
                payment_method_types=["card"],
                subscription_data={"items": [{"plan": get_subscription_plan()}]}
            )
            user.profile.checkout_session = checkout_session["id"]
            user.profile.save()
            success_url = reverse_lazy("thankyou")
            email_verification = settings.ACCOUNT_EMAIL_VERIFICATION
            _ = complete_signup(request, user, 
                                email_verification=email_verification,
                                success_url = success_url)            
            response_data = {"checkoutSessionId": checkout_session["id"]}
        else:
            logger.info(f"Form invalid. Errors: {form.errors}")
            response_data = {"error": form.errors}
        return JsonResponse(response_data, safe=False)
        
    else:
        return JsonResponse({"error": "Invalid Request"})

def checkout_success(request):
    stripe.api_key = settings.STRIPE_SK
    session_id = request.GET("session_id", "")
    if session_id:
        logger.info(f"Successful checkout: {session_id}")
    return render(request, 
                  "main/thankyou.html", 
                  context={"checkout_session_id": session_id})
    

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
            _ = complete_signup(request, user, 
                                email_verification=email_verification,
                                success_url = success_url)
            response_data = {"status": "success",
                             "subscription": subscription}
        else:
            logger.info(f"Form invalid. Errors: {form.errors}")
            response_data = {"status": "error", 
                             "errors": form.errors}
        return JsonResponse(response_data, safe=False)

    else:
        form = NNRSignupForm()
    return render(request, "account/signup.html", 
                           context={"form": form})

@login_required
def update_payment(request):
    user = request.user
    stripe.api_key = settings.STRIPE_SK
    if request.is_ajax():
        data = json.loads(request.body)
        payment_method = data["payment_method"]
        if user.is_staff:
            errmsg = "Payment not required"
            return JsonResponse({"status": "error",
                                 "error": {"message": errmsg}})
        
        if not user.profile.stripe_id:
            errmsg = "User has no customer id"
            return JsonResponse({"status": "error",
                                 "error" : {"message": errmsg}})

        pm, _ = update_customer_card(payment_method, 
                                     user.profile.stripe_id)        
        open_invoices = stripe.Invoice.list(customer=user.profile.stripe_id,
                                            status="open")     
        if not open_invoices:
            logger.info(f"No open invoices found for {user.username}")                                            
        # attempt to pay open invoices with new default payment method
        _ = [invoice.pay(expand=["payment_intent"]) 
             for invoice in open_invoices.data]
        newpay = (f"{pm.card.brand.title()} ending with {pm.card.last4} "
                  f"expires {pm.card.exp_month}/{pm.card.exp_year}")

        return JsonResponse({"status": "success", 
                             "message": "Default payment method updated",
                             "newPay" : newpay})

    if user.profile.stripe_id:    
        customer = stripe.Customer.retrieve(user.profile.stripe_id)
        pms = stripe.PaymentMethod.list(customer=user.profile.stripe_id, 
                                        type="card")
                            
        return render(request, "users/update_payment.html", 
                    context={"user": user,
                            "payment_methods": pms.data,
                            "customer": customer})
    else:
        return render(request, "users/update_payment.html", 
                    context={"user": user,
                            "payment_methods": [],
                            "customer": None})

@login_required
def confirm_payment(request):
    stripe.api_key = settings.STRIPE_SK
    user = request.user
    customer = stripe.Customer.retrieve(user.profile.stripe_id)
    invoice_id = customer.subscriptions.data[0].latest_invoice
    latest_invoice = stripe.Invoice.retrieve(invoice_id)
    invoice_url = latest_invoice.hosted_invoice_url
    return render(request, "users/confirm_payment.html",
                  context={"invoice_url": invoice_url})

def public_key(request):
    if request.is_ajax():
        return JsonResponse({"publicKey": settings.STRIPE_PK})
    else:
        return HttpResponseBadRequest("<h1>Bad Request</h1>")

@csrf_exempt
def webhook(request):
    webhook_secret = env("STRIPE_WEBHOOK_SECRET", "")
    payload = request.body
    event = None
    stripe.api_key = settings.STRIPE_SK
    if webhook_secret:
        signature = request.headers.get("stripe-signature")
        try: 
            event = stripe.Webhook.construct_event(
                payload=request.data, 
                sig_header=signature, 
                secret=webhook_secret)
        except Exception as e:
            logger.info(f"Could not parse event (webhook secret)")
            logger.info(e)
            return HttpResponse(status=400)
    else:
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
    elif event.type == "payment_method.updated":
        handle_payment_update(event)
    elif event.typ == "checkout.session.completed":
        handle_session_complete(event)
    else:
        logger.info(f"Received unhandled event: {event.type}")

    return HttpResponse(status=200)
