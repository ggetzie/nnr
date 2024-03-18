import json
import logging

from requests_oauthlib import OAuth1Session

logger = logging.getLogger(__name__)


def create_tweet(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
    message: str,
):
    payload = {"text": message}
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )
    response = oauth.post("https://api.twitter.com/2/tweets", json=payload)

    if response.status_code != 201:
        logger.error(
            "Error sending tweet: %s %s ", response.status_code, response.content
        )
        return

    logger.info(
        "Tweet sent: %s %s",
        response.status_code,
        json.dumps(response.json(), indent=2, sort_keys=True),
    )
