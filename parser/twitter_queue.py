import logging
from database import twittRedis, pastRedis, r
from twitter_creds import tweet_word, toot_word
from optv_api import double_check_newness, check_for_infos
import random
from dotenv import load_dotenv

load_dotenv()

def tweet_queue():
    
    tweetstop = twittRedis.get('meta:tweetstop')

    if tweetstop is None:
        logging.info('Tweet Skript wird gestartet')
        key = twittRedis.randomkey()

        if key:
            word = twittRedis.hget(key, "word").decode("utf-8")
            id = twittRedis.hget(key, "id").decode("utf-8") 

            redis_id = "protokoll:" + str(id)
            keys = r.hgetall(redis_id)
            
            if double_check_newness(word, keys):
                if send_tweet(word, keys):
                    return True
                else:
                    logging.debug('Wort konnte nicht gesendet werden.')
                    return False
            else:
                logging.info('Wort wurde bei OPTV gefunden.')
                remove_key(key)
                return False
        else:
            return False
    
    else:
        logging.info('Tweet Stopper existent.')
        return False



def send_tweet(word, keys):

    metadata = check_for_infos(word, keys)

    twitter_id = tweet_word(word, keys, metadata)
    mastodon_id = toot_word(word, keys, metadata)

    if not twitter_id:
        logging.debug('Es wurde keine Tweet ID gefunden.')
        return False
    elif not mastodon_id:
        logging.debug('Es wurde keine Mastodon ID gefunden.')
        return False
    else:
        return cleanup_db(word, twitter_id, mastodon_id)

def cleanup_db(word, twitter_id, mastodon_id):

    set_tweet_stopper()

    # Ins Archiv bewegen
    try:
        twittRedis.move(word, 2)
        pastRedis.hset(word, "tweet_id", twitter_id)
        pastRedis.hset(word, "mastodon_id", mastodon_id)
        logging.info('Wort wurde ins Archiv verschoben.')
        return True
    except Exception as e:
        logging.exception(e)
        return False

def remove_key(key):
    try:
        twittRedis.delete(key)
        return True
    except Exception as e:
        logging.exception(e)
        raise

def set_tweet_stopper():

    expireTime = 60*round(random.randrange(55,120))
    twittRedis.set('meta:tweetstop', 1 , ex=expireTime)
    logging.info('Tweet-Stopper wurde gesetzt.')

    return True










if __name__ == "__main__":
    logging.basicConfig(
        filename='bundestagbot/parser/twitter.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')    
    tweet_queue()