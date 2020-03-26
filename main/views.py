from allauth.account.utils import complete_signup

from dateutil.relativedelta import relativedelta
import environ

from django.conf import settings
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import (CreateView, UpdateView, DeleteView, ListView,
                                  DetailView, FormView)
from main.forms import NNRSignupForm

from main.models import Profile

from main.payments import (handle_payment_success, handle_payment_action,
                           handle_payment_failure, handle_payment_update,
                           update_customer_card, handle_session_complete,
                           handle_subscription_updated, 
                           handle_subscription_deleted)

from main.utils import (get_trial_end, get_subscription_plan)

from mixins import ValidUserMixin

import datetime
import logging
import json
import stripe

env = environ.Env()
logger = logging.getLogger(__name__)

DOMAIN_URL = "http://nnr" if settings.DEBUG else "https://nononsense.recipes"

def public_key(request):
    if request.is_ajax():
        return JsonResponse({"publicKey": settings.STRIPE_PK})
    else:
        return HttpResponseBadRequest("<h1>Bad Request</h1>")                            

@login_required
def create_checkout_session(request):
    if not request.is_ajax():
        return HttpResponse("Bad Request")
    stripe.api_key = settings.STRIPE_SK
    success_url=(DOMAIN_URL + 
                 reverse("main:checkout_success") + 
                 "?session_id={CHECKOUT_SESSION_ID}")
    cancel_url=DOMAIN_URL+reverse("main:payment")
    if request.user.profile.stripe_id:
        # User already had a subscription that expired. No free trial.
        checkout_session = stripe.checkout.Session.create(
            customer=request.user.profile.stripe_id,
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method_types=["card"],
            subscription_data={
                    "items": [{
                        "plan": get_subscription_plan()
                        }],
                    "trial_from_plan": False
                }
        )
    else:
        # New user, include free trial
        checkout_session = stripe.checkout.Session.create(
                customer_email=request.user.email,
                success_url=success_url,
                cancel_url=cancel_url,
                payment_method_types=["card"],
                subscription_data={
                    "items": [{
                        "plan": get_subscription_plan()
                        }],
                    "trial_from_plan": True
                }
        )
    request.user.profile.checkout_session = checkout_session["id"]
    request.user.profile.save()
    return JsonResponse({"checkoutSessionId": checkout_session["id"]})

def checkout_success(request):
    stripe.api_key = settings.STRIPE_SK
    session_id = request.GET.get("session_id", "")
    if session_id:
        logger.info(f"Successful checkout: {session_id}")
    return render(request, 
                  "main/thankyou.html", 
                  context={"checkout_session_id": session_id})
    
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


@require_POST                            
@login_required
def cancel_subscription(request):
    """
    User wants to turn off automatic renewal. 
    Subscription will expire at end date.
    """
    stripe.api_key = settings.STRIPE_SK
    stripe_id = request.user.profile.stripe_id
    subs = stripe.Subscription.list(customer=stripe_id)
    if subs.data:
        _ = stripe.Subscription.modify(subs.data[0].id,
                                       cancel_at_period_end=True)
        end_date = datetime.datetime.fromtimestamp(subs.data[0].current_period_end)
        msg = f"""
              Automatic renewal has been turned off for your subscription.
              Your subscription will expire on {end_date:%B %d, %Y}.
              Your account will remain active until then.
              """
        messages.warning(request, msg)
    else:
        messages.info(request, "Could not find any active subscription")
    return redirect("users:detail", username=request.user.username)


@require_POST
@login_required
def reactivate_subscription(request):
    """
    User has turned off automatic renewal and wants to turn it back on
    """
    stripe.api_key = settings.STRIPE_SK
    stripe_id = request.user.profile.stripe_id
    subs = stripe.Subscription.list(customer=stripe_id)
    if subs.data:
        _ = stripe.Subscription.modify(subs.data[0].id,
                                       cancel_at_period_end=False)
        end_date = datetime.datetime.fromtimestamp(subs.data[0].current_period_end)
        msg = f"""
              Automatic renewal has been turned on for your subscription.
              Your subscription will be renewed on {end_date:%B %d, %Y}.
              """
        messages.success(request, msg)                                       
    else:
        messages.info(request, "Could not find any active subscription")
    return redirect("users:detail", username=request.user.username)


@login_required
def confirm_payment(request):
    stripe.api_key = settings.STRIPE_SK
    user = request.user
    customer = stripe.Customer.retrieve(user.profile.stripe_id)
    try:
        invoice_id = customer.subscriptions.data[0].latest_invoice
        latest_invoice = stripe.Invoice.retrieve(invoice_id)
        invoice_url = latest_invoice.hosted_invoice_url
        return render(request, "users/confirm_payment.html",
                    context={"invoice_url": invoice_url})
    except IndexError:
        # no outstanding invoice
        return redirect("home")

@csrf_exempt
def webhook(request):
    webhook_secret = env("STRIPE_WEBHOOK_SECRET", default="")
    payload = request.body
    event = None
    stripe.api_key = settings.STRIPE_SK
    if webhook_secret:
        signature = request.META.get("HTTP_STRIPE_SIGNATURE")
        logger.info(request.META)
        try: 
            event = stripe.Webhook.construct_event(
                payload=json.loads(payload),
                sig_header=signature, 
                secret=webhook_secret)
        except Exception as e:
            logger.error(f"Could not parse event (webhook secret)")
            logger.error(e)
            return HttpResponse(status=400)
    else:
        try:
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
        except ValueError:
            logger.error(f"Could not parse event")
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
    elif event.type == "checkout.session.completed":
        handle_session_complete(event)
    elif event.type == "customer.subscription.updated":
        handle_subscription_updated(event)
    elif event.type == "customer.subscription.deleted":
        handle_subscription_deleted(event)
    else:
        logger.info(f"Received unhandled event: {event.type}")

    return HttpResponse(status=200)
