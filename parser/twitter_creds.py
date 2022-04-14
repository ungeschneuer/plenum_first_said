# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
"""
import logging
from dotenv import load_dotenv
import os
from database import r, twittRedis
import tweepy
from mastodon import Mastodon

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
MastodonAPI = Mastodon(access_token = os.environ.get('MASTODON_FIRST_ACCESSTOKEN'),  api_base_url="https://mastodon.social")
MastodonKontextAPI = Mastodon(access_token = os.environ.get('MASTODON_KONTEXT_ACCESSTOKEN'),  api_base_url="https://mastodon.social")


def delete_from_queue(word):
    twittRedis.hdel(word)
    return True


def tweet_word(word, id):
    redis_id = "protokoll:" + str(id)
    
    keys = r.hgetall(redis_id)

    try:
        status = twitterAPI.update_status(word)
        context_status = contextAPI.update_status(
            "@{} #{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet man unter {}".format(
                status.user.screen_name,
                word,
                keys[b'titel'].decode('UTF-8'),
                keys[b'datum'].decode('UTF-8'),
                keys[b'pdf_url'].decode('UTF-8')),
            in_reply_to_status_id=status.id)
        
        if context_status:
            logging.info('Tweet wurde gesendet.')
            return toot_word(word, keys)
        else:
            return False
        
    except UnicodeDecodeError as e:
        logging.exception(e)
        return False
    except tweepy.TweepError as e:
        logging.exception(e)
        
        if e.args[0][0]['code'] == 187:
            delete_from_queue(word)
            return False
        
        return False
    



def toot_word(word, keys):
    try: 
        toot_status = MastodonAPI.toot(word)

        context_status = MastodonKontextAPI.status_post("#{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet man unter {}".format(
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                    in_reply_to_id = toot_status["id"])

        logging.info('Toot wurde gesendet.')
        return context_status
    except Exception as e:
        logging.exception(e)
        return False


def tweet_text(text):
        trends = twitterAPI.trends_place(23424829)
        trend_array = []

        for trend in trends[0]["trends"]:
            trend_array.append(trend["name"].strip('#'))

        for word in trend_array:
            db_word = r.hgetall('word:' + word)
            if db_word:
                return True

if __name__ == "__main__":
    tweet_text("test")
