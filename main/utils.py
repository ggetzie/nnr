import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings

import logging

logger = logging.getLogger(__name__)

STOPWORDS = {"i","me","my","myself","we","our","ours","ourselves","you","your",
             "yours", "yourself","yourselves","he","him","his","himself","she",
             "her","hers","herself","it","its","itself","they","them","their",
             "theirs","themselves","what","which","who","whom","this","that",
             "these","those","am","is","are","was","were","be","been","being",
             "have","has","had","having","do","does","did","doing","a","an",
             "the","and","but","if","or","because","as","until","while","of",
             "at","by","for","with","about","against","between","into","through",
             "during","before","after","above","below","to","from","up","down",
             "in","out","on","off","over","under","again","further","then",
             "once","here","there","when","where","why","how","all","any","both",
             "each","few","more","most","other","some","such","no","nor","not",
             "only","own","same","so","than","too","very","s","t","can","will",
             "just","don","should","now", "best"}

def sortify(slug, stopwords=STOPWORDS):
    title_words = slug.split("-")
    for i, word in enumerate(title_words):
        if word in stopwords:
            continue
        else:
            first_letter = "0-9" if word[0].isdigit() else word[0].upper()
            sort_title = "-".join(title_words[i:])
            return first_letter, sort_title

def get_trial_end():
    if settings.DEBUG:
        trial_period = relativedelta(minutes=1)
    else:
        trial_period = relativedelta(days=30)
    trial_end = datetime.datetime.now() + trial_period
    return int(trial_end.timestamp())

def get_subscription_plan():
    if settings.DEBUG:
        # test plan
        plan = "plan_GE5qJjPJHeV0Hn"
    else:
        # production plan
        plan = "plan_G9ZcHdJbqG4WBs"
    return plan
    
