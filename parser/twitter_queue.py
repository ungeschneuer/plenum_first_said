import logging
from database import twittRedis, pastRedis, r
from twitter_creds import tweet_word, toot_word, delete_from_queue
from optv_api import double_check_newness, check_for_infos
import random
from dotenv import load_dotenv

load_dotenv()


# Organisiert das Senden von Tweets
# Wenn irgendeine Art von Fehler beim Senden passiert, wird das Wort entfernt. 
# TODO Granularere Fehlerbehandlung
def tweet_queue():
    
    tweetstop = twittRedis.get('meta:tweetstop')

    if tweetstop is None:
        logging.info('Tweet Skript wird gestartet')
        key = twittRedis.randomkey()

        if key:
            word = twittRedis.hget(key, "word").decode("utf-8")
            id = twittRedis.hget(key, "id").decode("utf-8") 
            logging.info("Wort '" + word + "' wird veröffentlicht.")

            redis_id = "protokoll:" + str(id)
            protokoll_keys = r.hgetall(redis_id)
            
            if double_check_newness(word, protokoll_keys):
                if send_tweet(word, protokoll_keys):
                    return True
                else:
                    logging.debug('Wort konnte nicht gesendet werden.')
                    delete_from_queue(word)
                    return False
            else:
                logging.info('Wort wurde bei OPTV gefunden.')
                delete_from_queue(word)
                return False
        else:
            logging.info("Key does not exist. Key: " + str(key))
            return False
    
    else:
        return False



def send_tweet(word, keys):

    metadata = check_for_infos(word, keys)

    twitter_id = tweet_word(word, keys, metadata)


    if twitter_id:
        mastodon_id = toot_word(word, keys, metadata)

        if not mastodon_id:
            logging.debug('Es wurde keine Mastodon ID gefunden.')
            return False
    else:
        logging.debug('Es wurde keine Tweet ID gefunden.')
        return False

    
    return cleanup_db(word, twitter_id, mastodon_id)

def cleanup_db(word, twitter_id, mastodon_id):

    set_tweet_stopper()

    # Ins Archiv bewegen
    try:
        twittRedis.move(word, 2)
        pastRedis.hset(word, "tweet_id", twitter_id)
        pastRedis.hset(word, "mastodon_id", mastodon_id)
        delete_from_queue(word)
        logging.info('Wort wurde ins Archiv verschoben.')
        return True
    except Exception as e:
        logging.exception(e)
        return False

def set_tweet_stopper():

    expireTime = 60*round(random.randrange(55,120))
    twittRedis.set('meta:tweetstop', 1 , ex=expireTime)
    logging.info('Tweet-Stopper wurde gesetzt auf ' + str(expireTime/60) + ' Minuten.')

    return True










if __name__ == "__main__":
    logging.basicConfig(
        filename='bundestagbot/parser/twitter.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')    
    tweet_queue()