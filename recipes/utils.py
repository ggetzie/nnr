import datetime 
import json
import os

import requests

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

def spacing(text):
    """
    Add blank line before all uppercase lines
    """
    outlines = []
    lines = text.split("\n")
    last = ""
    for line in lines:
        if line.isupper() and last.isprintable():
            outlines.append("")
        outlines.append(line)
        last = line
    return "\n".join(outlines)

def utc_now():
    return datetime.datetime.now(tz=datetime.timezone.utc)

FB_GRAPH_URL = "https://graph.facebook.com"

def get_fb_long_token(short_token):
    app_id = os.environ["FB_APP_ID"]
    app_secret = os.environ["FB_APP_SECRET"]
    url = (
        f"{FB_GRAPH_URL}/oauth/access_token?grant_type=fb_exchange_token"
        f"&client_id={app_id}&client_secret={app_secret}"
        f"&fb_exchange_token={short_token}"
    )
    r = requests.get(url)
    return r

def get_fb_page_token(long_token):
    page_id = os.environ["FB_PAGE_ID"]
    r = requests.get(f"{FB_GRAPH_URL}/{page_id}?fields=access_token&access_token={long_token}")
    return r

def test_post_recipe(recipe):
    message = f"{recipe.text_only()}\nhttps://nononsense.recipes/{recipe.title_slug}/"
    page_id = os.environ["FB_PAGE_ID"]
    page_token = os.environ["FB_PAGE_TOKEN"]
    r = requests.post(
        f"{FB_GRAPH_URL}/{page_id}/feed",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "message": message,
            "access_token": page_token
        }))
    return r
    

