import datetime
from dateutil.relativedelta import relativedelta

from .models import Profile
import logging

logger = logging.getLogger(__name__)

def handle_payment_success(event):
    customer_id = event.data.object.customer
    logger.info("handling payment success")
    logger.info(f"customer_id={customer_id} paid {event.object.amount_paid}")
    profile = Profile.objects.get(stripe_id=customer_id)
    if event.object.amount_paid > 0:
        profile.payment_status = 3
        new_end = datetime.date.today() + relativedelta(years=1)
        profile.subscription_end = new_end
    elif event.object.amount_paid == 0:
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
    profile = Profile.objects.get(stripe_id=event.data.objects.customer)
    profile.payment_status = 0
    profile.save()