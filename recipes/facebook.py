from logging import getLogger
import requests

logger = getLogger(__name__)


def list_pages(fb_user_id, fb_user_token):
    url = f"https://graph.facebook.com/{fb_user_id}/accounts"
    r = requests.get(url, params={"access_token": fb_user_token})
    if r.status_code != 200:
        logger.error("Error getting facebook pages: %s %s ", r.status_code, r.content)
    return r


def post_to_page(fb_page_id, fb_page_token, message, link=None):
    url = f"https://graph.facebook.com/{fb_page_id}/feed"
    r = requests.post(
        url, data={"message": message, "link": link, "access_token": fb_page_token}
    )
    if r.status_code != 200:
        logger.error("Error posting to facebook: %s %s ", r.status_code, r.content)
    return r
