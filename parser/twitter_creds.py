# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
"""
from sentry_sdk import capture_exception
from dotenv import load_dotenv
import os
from database import r
import tweepy

load_dotenv()

def TwitterApi():
    auth =  tweepy.OAuthHandler(consumer_key=os.environ.get('FIRST_CONSUMER_KEY'),consumer_secret=os.environ.get('FIRST_CONSUMER_SECRET'))
    auth.set_access_token(key=os.environ.get('FIRST_ACCESS_TOKEN_KEY'), secret=os.environ.get('FIRST_ACCESS_TOKEN_SECRET'))
    return tweepy.API(auth)


def ContextTwitterApi():
    auth =  tweepy.OAuthHandler(consumer_key=os.environ.get('CONTEXT_CONSUMER_KEY'),consumer_secret=os.environ.get('CONTEXT_CONSUMER_SECRET'))
    auth.set_access_token(key=os.environ.get('CONTEXT_ACCESS_TOKEN_KEY'), secret=os.environ.get('CONTEXT_ACCESS_TOKEN_SECRET'))
    return tweepy.API(auth)



twitterAPI = TwitterApi()
contextAPI = ContextTwitterApi()



def tweet_word(word, id):
    redis_id = "protokoll:" + str(id)
    
    key = r.hgetall(redis_id)


    try:
        status = twitterAPI.update_status(word)
        context_status = contextAPI.update_status(
            "@{} \"{}\" tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet man unter {}".format(
                status.user.screen_name,
                word,
                r.hget(redis_id, 'titel').decode('utf-8'),
                r.hget(redis_id, 'datum').decode('utf-8'),
                r.hget(redis_id, 'pdf_url').decode('utf-8')),
            in_reply_to_status_id=status.id)
        
        if context_status:
            return status.id
        else:
            return False
        
    except UnicodeDecodeError as e:
        capture_exception(e)
        return False
    except twitter.TwitterError as e:
        capture_exception(e)
        return False
