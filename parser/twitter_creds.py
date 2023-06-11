# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
"""
import logging
from dotenv import load_dotenv
import os
from database import r, postRedis, delete_from_queue
import tweepy

load_dotenv()


def TwitterApi():
    return tweepy.Client( consumer_key= os.environ.get('FIRST_CONSUMER_KEY'),
                        consumer_secret= os.environ.get('FIRST_CONSUMER_SECRET'),
                        access_token= os.environ.get('FIRST_ACCESS_TOKEN_KEY'),
                        access_token_secret= os.environ.get('FIRST_ACCESS_TOKEN_SECRET'))

def ContextTwitterApi():
    return tweepy.Client( consumer_key= os.environ.get('CONTEXT_CONSUMER_KEY'),
                        consumer_secret= os.environ.get('CONTEXT_CONSUMER_SECRET'),
                        access_token= os.environ.get('CONTEXT_ACCESS_TOKEN_KEY'),
                        access_token_secret= os.environ.get('CONTEXT_ACCESS_TOKEN_SECRET'))


twitterAPI = TwitterApi()
contextAPI = ContextTwitterApi()


def tweet_word(word, keys, metadata):
    
    try:
        
        logging.info('Tweete: ' + word)

        status = twitterAPI.create_tweet(text=word)

        logging.info("ID: " +  status.data['id'])

        if metadata:
            context_status = contextAPI.create_tweet(
                text="#{} tauchte zum ersten Mal im {} am {} auf. Es wurde im Rahmen der Rede von {} ({}) gesagt.\n\nVideo: {}".format(
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    metadata['speaker'],
                    metadata['party'],
                    metadata['link']),
                in_reply_to_tweet_id=status.data['id'])

            second_context_status = contextAPI.create_tweet(
                text="Das {} findet sich als PDF unter {}".format(
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                in_reply_to_tweet_id=context_status.data['id'])

        else: 
            context_status = contextAPI.create_tweet(
               text="#{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet sich unter {}".format(
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                in_reply_to_tweet_id=status.data['id'])
        
        if status and context_status:
            logging.info('Tweet wurde gesendet:' + str(status.data['id']))
            return status.data['id']
        else:
            logging.debug('Tweet konnte nicht gesendet werde.')
            return False
        
    except UnicodeDecodeError as e:
        logging.exception(e)
        return False
    except tweepy.TwitterServerError as e:
        logging.exception(e)
        return False
    except tweepy.HTTPException as e:
        logging.exception(e)
        if e.api_codes[0] == 187:
            delete_from_queue(word)
        return False
    except tweepy.TweepyException as e:
        logging.exception(e)
        return False
    except tweepy.errors.Forbidden as e:
        logging.exception(e)
        return False


    


