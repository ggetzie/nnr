import datetime
from dateutil.relativedelta import relativedelta
import environ

from django.conf import settings


from .models import Profile
import logging
import stripe

logger = logging.getLogger(__name__)
env = environ.Env()

def get_product_id():
    return "prod_GE5pYP4NwXPmjc" if settings.DEBUG else "prod_G9ZbbNuFBeBF1Y"

def display_plan(plan):
    """Print out the payment plan name and details from stripe API plan object"""
    return (f"{plan.metadata.display_name} - ${plan.amount / 100:.2f} "
            f"USD per {plan.interval}")

def get_payment_plans():
    stripe.api_key = settings.STRIPE_SK
    plans = stripe.Plan.list(active=True, product=get_product_id())
    return [(p.id, display_plan(p)) for p in plans["data"]]

def handle_payment_success(event):
    customer_id = event.data.object.customer
    customer_email = event.data.object.customer_email
    amount_paid = event.data.object.amount_paid
    logger.info("handling payment success")
    logger.info(f"customer_id={customer_id} paid {amount_paid}")
    try:
        profile = Profile.objects.get(stripe_id=customer_id)
    except Profile.DoesNotExist:
        profile = Profile.objects.get(user__email=customer_email)
    if amount_paid > 0:
        profile.payment_status = 3
        new_end = datetime.date.today() + relativedelta(years=1)
        profile.subscription_end = new_end
    elif amount_paid == 0:
        profile.payment_status = 2
    else:
        pass    
    profile.sync_subscription()
    profile.save()

def handle_payment_action(event):
    logger.info("handling payment action")
    try:
        profile = Profile.objects.get(stripe_id=event.data.object.customer)
    except Profile.DoesNotExist:
        customer_email = event.data.object.customer_email
        profile = Profile.objects.get(user__email=customer_email)
    profile.payment_status = 1
    profile.sync_subscription()
    profile.save()

def handle_payment_failure(event):
    logger.info("handling payment failure")
    try:
        profile = Profile.objects.get(stripe_id=event.data.object.customer)
    except Profile.DoesNotExist:
        customer_email = event.data.object.customer_email
        profile = Profile.objects.get(user__email=customer_email)
    profile.payment_status = 0
    profile.sync_subscription()
    profile.save()

def handle_payment_update(event):
    logger.info("handling updated payment method")

def update_customer_card(payment_id, customer_id):
    stripe.api_key = settings.STRIPE_SK
    # remove old payment methods
    old_cards = stripe.PaymentMethod.list(customer=customer_id, type="card")
    for card in old_cards.data:
        stripe.PaymentMethod.detach(card.id)
    
    new_card = stripe.PaymentMethod.attach(payment_id, customer=customer_id)
    default = stripe.Customer.modify(customer_id,
                                     invoice_settings = {
                                         "default_payment_method": payment_id
                                     })
    return new_card, default

def handle_session_complete(event):
    logger.info("Checkout Session completed")
    stripe.api_key = settings.STRIPE_SK
    session_id = event.data.object.id
    customer_email = event.data.object.customer_email
    try:
        profile = Profile.objects.get(checkout_session=session_id)
    except Profile.DoesNotExist:
        profile = Profile.objects.get(user__email=customer_email)
    profile.checkout_session = ""
    if not profile.stripe_id:
        # No existing stripe id means new user, complete signup
        profile.stripe_id = event.data.object.customer
        profile.payment_status = 2
    profile.save()
    profile.sync_subscription()
        
def handle_subscription_updated(event):
    stripe_id = event.data.object.customer
    try:
        profile = Profile.objects.get(stripe_id=stripe_id)
    except Profile.DoesNotExist:
        stripe.api_key = settings.STRIPE_SK
        customer = stripe.Customer.retrieve(stripe_id)
        customer_email = customer.email
        profile = Profile.objects.get(user__email=customer_email)
        profile.stripe_id = stripe_id
        profile.save()
    profile.sync_subscription()

def handle_subscription_created(event):
    stripe_id = event.data.object.customer
    try:
        profile = Profile.objects.get(stripe_id=stripe_id)
    except Profile.DoesNotExist:
        stripe.api_key = settings.STRIPE_SK
        customer = stripe.Customer.retrieve(stripe_id)
        customer_email = customer.email
        profile = Profile.objects.get(user__email=customer_email)
        profile.stripe_id = stripe_id
        profile.save()
    profile.sync_subscription()    

def handle_subscription_deleted(event):
    logger.info("Handling deleted subscription")
    stripe_id = event.data.object.customer
    try:
        profile = Profile.objects.get(stripe_id=stripe_id)
        profile.sync_subscription()
        profile.subscription_end = datetime.date.today()
    except Profile.DoesNotExist:
        # user must have been deleted before stripe customer /shrug?
        pass