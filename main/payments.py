import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings

from .models import Profile
import logging
import stripe

logger = logging.getLogger(__name__)

def handle_payment_success(event):
    customer_id = event.data.object.customer
    amount_paid = event.data.object.amount_paid
    logger.info("handling payment success")
    logger.info(event)
    logger.info(f"customer_id={customer_id} paid {amount_paid}")
    profile = Profile.objects.get(stripe_id=customer_id)
    if amount_paid > 0:
        profile.payment_status = 3
        new_end = datetime.date.today() + relativedelta(years=1)
        profile.subscription_end = new_end
    elif amount_paid == 0:
        profile.payment_status = 2
    else:
        pass    
    profile.save()

def handle_payment_action(event):
    logger.info("handling payment action")
    profile = Profile.objects.get(stripe_id=event.data.object.customer)
    profile.payment_status = 1
    profile.save()

def handle_payment_failure(event):
    logger.info("handling payment failure")
    profile = Profile.objects.get(stripe_id=event.data.object.customer)
    profile.payment_status = 0
    profile.save()

def handle_payment_update(event):
    logger.info("handling updated payment method")
    # get profile from stripe customer id
    # check if customer has outstanding invoice with failed payment
    # if so, retry payment with new payment method
    # if successful, set payment status to success
    # otherwise do nothing

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