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
from time import sleep

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
    if twittRedis.delete(word):
        return True
    else: 
        return False


def tweet_word(word, keys, metadata):
    
    try:
        status = twitterAPI.update_status(word)

        if metadata:
            context_status = contextAPI.update_status(
                "@{} #{} tauchte zum ersten Mal im {} am {} auf. Es wurde von {} ({}) gesagt.\n\nVideo: {}".format(
                    status.user.screen_name,
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    metadata['speaker'],
                    metadata['party'],
                    metadata['link']),
                in_reply_to_status_id=status.id)

            second_context_status = contextAPI.update_status(
                "@{} Das {} findet sich als PDF unter {}".format(
                    context_status.user.screen_name,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                in_reply_to_status_id=context_status.id)

        else: 
            context_status = contextAPI.update_status(
                "@{} #{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet sich unter {}".format(
                    status.user.screen_name,
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                in_reply_to_status_id=status.id)
        
        if status and context_status:
            logging.info('Tweet wurde gesendet:' + context_status.id_str)
            return status.id
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


    


# Mastodon API is a bit wobbly so a fix with while loops 
def toot_word(word, keys, metadata):

    # Max tries to get posting trough
    patience = 0
    
    #Posts Word
    while True:
        try: 
            toot_status = MastodonAPI.toot(word)

        except Exception as e:
            logging.exception(e)
            sleep(120)
            patience += 1
            continue
        if patience > 50:
            logging.info('Maximale Versuche wurde überschritten.')
            return False
        else:
            break

    
    # Posts Context
    # Metada is information from OPTV
    if metadata:
        while True:
            try:
                context_status = MastodonKontextAPI.status_post("#{} tauchte zum ersten Mal im {} am {} auf. Es wurde von {} ({}) gesagt.\n\nVideo: {}".format(
                        word,
                        keys[b'titel'].decode('UTF-8'),
                        keys[b'datum'].decode('UTF-8'),
                        metadata['speaker'],
                        metadata['party'],
                        metadata['link']),
                        in_reply_to_id = toot_status["id"])
            except Mastodon.MastodonNotFoundError as e:
                logging.exception(e)
                sleep(120)
                patience += 1 
                continue
            except Exception as e:
                logging.exception(e)
                return False
            if patience > 50:
                logging.info('Maximale Versuche wurde überschritten.')
                return False
            else:
                break



        if context_status.user:
            while True:
                try:
                    second_context_status = MastodonKontextAPI.status_post(
                        "Das {} findet sich als PDF unter {}".format(
                            context_status.user.screen_name,
                            keys[b'titel'].decode('UTF-8'),
                            keys[b'pdf_url'].decode('UTF-8')),
                        in_reply_to_status_id=context_status.id)
                except Mastodon.MastodonNotFoundError as e:
                    logging.exception(e)
                    sleep(120)
                    patience += 1
                    continue
                except Exception as e:
                    logging.exception(e)
                    return False
                if patience > 50:
                    logging.info('Maximale Versuche wurde überschritten.')
                    return False
                else:
                    break

        else:
            logging.info(context_status)
            return False

    else:
        while True:
            try:     
                context_status = MastodonKontextAPI.status_post("#{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet sich unter {}".format(
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                    in_reply_to_id = toot_status["id"])
            except Mastodon.MastodonNotFoundError as e:
                logging.exception(e)
                sleep(120)
                patience += 1 
                continue
            except Exception as e:
                logging.exception(e)
                return False
            if patience > 50:
                logging.info('Maximale Versuche wurde überschritten.')
                return False
            else:
                break


    logging.info('Toot wurde erfolgreich gesendet.')
    return toot_status["id"]


