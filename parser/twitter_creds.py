# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
"""
import twitter
from sentry_sdk import capture_exception
from dotenv import load_dotenv
import os

load_dotenv()

def TwitterApi():
    return twitter.api.Api(consumer_key=os.environ.get('FIRST_CONSUMER_KEY'),
                consumer_secret=os.environ.get('FIRST_CONSUMER_SECRET'),
                access_token_key=os.environ.get('FIRST_ACCESS_TOKEN_KEY'),
                access_token_secret=os.environ.get('FIRST_ACCESS_TOKEN_SECRET'))



twitterAPI = TwitterApi()



def tweet_word(word, sitzung, url):
    try:
        status = twitterAPI.PostUpdate(word)
        twitterAPI.PostUpdate(
            "Das Wort tauchte in der Sitzung {} zum ersten Mal auf. Das Protokoll findet man unter {}".format(
                sitzung,
                url),
            in_reply_to_status_id=status.id,
            verify_status_length=False)
    except UnicodeDecodeError as e:
        capture_exception(e)
        return False
    except twitter.TwitterError as e:
        print(e)
        capture_exception(e)
        return False

    return True

