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


def tweet_word(word, keys, metadata):
    
    try:
        status = twitterAPI.update_status(word)

        if metadata:
            context_status = contextAPI.update_status(
                """@{} #{} tauchte zum ersten Mal im {} am {} auf. Es wurde von {} ({}) gesagt. 
                
                Protokoll: {}
                Video: {}""".format(
                    status.user.screen_name,
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    metadata['speaker'],
                    metadata['party'],
                    keys[b'pdf_url'].decode('UTF-8'),
                    metadata['link']),
                in_reply_to_status_id=status.id)

        else: 
            context_status = contextAPI.update_status(
                "@{} #{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet sich unter {}".format(
                    status.user.screen_name,
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                in_reply_to_status_id=status.id)
        
        if context_status:
            logging.info('Tweet wurde gesendet:' + context_status)
            return status.id
        else:
            logging.debug('Tweet konnte nicht gesendet werde.')
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
    



def toot_word(word, keys, metadata):
    try: 
        toot_status = MastodonAPI.toot(word)

        if metadata:
            context_status = MastodonKontextAPI.status_post("""@{} #{} tauchte zum ersten Mal im {} am {} auf. Es wurde von {} ({}) gesagt. 
                
                Protokoll: {}
                Video: {}""".format(
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    metadata['speaker'],
                    metadata['party'],
                    keys[b'pdf_url'].decode('UTF-8'),
                    metadata['link']),
                    in_reply_to_id = toot_status["id"])

        else:     
            context_status = MastodonKontextAPI.status_post("#{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet sich unter {}".format(
                word,
                keys[b'titel'].decode('UTF-8'),
                keys[b'datum'].decode('UTF-8'),
                keys[b'pdf_url'].decode('UTF-8')),
                in_reply_to_id = toot_status["id"])

        if context_status:
            logging.info('Toot wurde gesendet.')
            return toot_status["id"]
        else:
            logging.debug('Toot konnte nicht gesendet werde.')
            return False
    except Exception as e:
        logging.exception(e)
        return False



if __name__ == "__main__":
