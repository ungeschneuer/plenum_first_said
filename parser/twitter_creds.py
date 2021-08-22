# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
"""
import twitter
from sentry_sdk import capture_exception
from dotenv import load_dotenv
import os
from database import r

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



def tweet_word(word, id):
    redis_id = "protokoll:" + str(id)
    
    key = r.hgetall(redis_id)


    try:
        status = twitterAPI.PostUpdate(word)
        context_status = contextAPI.PostUpdate(
            "@{} \"{}\" tauchte zum ersten Mal im {} auf. Das Protokoll findet man unter {}".format(
                status.user.screen_name,
                word,
                r.hget(redis_id, 'titel').decode('utf-8'),
                r.hget(redis_id, 'pdf_url').decode('utf-8')),
            in_reply_to_status_id=status.id,
            verify_status_length=False)
        
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
