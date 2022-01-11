import logging
from database import twittRedis, pastRedis
from twitter_creds import tweet_word, toot_word
import random
from dotenv import load_dotenv    

load_dotenv()

def tweet_queue():
    
    tweetstop = twittRedis.get('meta:tweetstop')

    if tweetstop is None:
        key = twittRedis.randomkey()
        if key and not send_tweet(key):
            logging.debug('Tweet konnte nicht gesendet werden.')
            return False
        return True    
    return False

def send_tweet(key):
    word = twittRedis.hget(key, "word").decode("utf-8")
    id = twittRedis.hget(key, "id").decode("utf-8") 


    status_id = tweet_word(word, id)

    if not status_id:
        logging.debug('Tweet konnte nicht gesendet werden.')
        return False
    
    return cleanup_db(word, status_id)

def cleanup_db(word, status_id):

    set_tweet_stopper()

    # Ins Archiv bewegen
    try:
        twittRedis.move(word, 2)
        pastRedis.hset(word, "tweet_id", status_id)
        logging.info('Tweet wurde ins Archiv verschoben.')
        return True
    except Exception as e:
        logging.exception(e)
        return False

def set_tweet_stopper():

    expireTime = 60*round(random.randrange(55,120))
    twittRedis.set('meta:tweetstop', 1 , ex=expireTime)
    logging.info('Tweet stopper wurde gesetzt.')

    return True













if __name__ == "__main__":
    logging.basicConfig(filename='tweet.log', level=logging.DEBUG)
    logging.info('Tweet_Skript wird gestartet')
    tweet_queue()
    logging.info('Tweet_Skript wird beendet')
