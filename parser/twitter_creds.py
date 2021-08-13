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


def ContextTwitterApi():
    return twitter.api.Api(consumer_key=os.environ.get('CONTEXT_CONSUMER_KEY'),
                consumer_secret=os.environ.get('CONTEXT_CONSUMER_SECRET'),
                access_token_key=os.environ.get('CONTEXT_ACCESS_TOKEN_KEY'),
                access_token_secret=os.environ.get('CONTEXT_ACCESS_TOKEN_SECRET'))



twitterAPI = TwitterApi()
contextAPI = ContextTwitterApi()



def tweet_word(word, sitzung, url):
    try:
        status = twitterAPI.PostUpdate(word)
        context_status = contextAPI .PostUpdate(
            "@{} \"{}\" tauchte zum ersten Mal in Sitzung {} auf. Das Protokoll findet man unter {}".format(
                status.user.screen_name,
                word,
                sitzung,
                url),
            in_reply_to_status_id=status.id,
            verify_status_length=False)
        
        if context_status:
            return True
        else:
            return False
        
    except UnicodeDecodeError as e:
        capture_exception(e)
        return False
    except twitter.TwitterError as e:
        capture_exception(e)
        return False

    return True

