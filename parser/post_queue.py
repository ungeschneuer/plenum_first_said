import logging
from database import postRedis, pastRedis, r, delete_from_queue
# from twitter_creds import tweet_word
from mastodon_cred import toot_word
from optv_api import double_check_newness, check_for_infos
import random
from dotenv import load_dotenv

load_dotenv()


# Organisiert das Senden von Tweets
# Wenn irgendeine Art von Fehler beim Senden passiert, wird das Wort entfernt. 
def post_from_queue():
    
    tweetstop = postRedis.get('meta:tweetstop')

    if tweetstop is None:
        set_tweet_stopper()
        logging.info('Tweet Skript wird gestartet')
        key = postRedis.randomkey()

        if key == b'meta:tweetstop':
            logging.info('Keine Wörter in der Queue.')
            return False

        if key:
            word = postRedis.hget(key, "word").decode("utf-8")
            id = postRedis.hget(key, "id").decode("utf-8") 
            logging.info("Wort '" + word + "' wird veröffentlicht.")

            redis_id = "protokoll:" + str(id)
            protokoll_keys = r.hgetall(redis_id)
            
            if double_check_newness(word, protokoll_keys):
                if send_word(word, protokoll_keys):
                    return True
                else:
                    logging.debug('Wort konnte nicht gesendet werden.')
                    delete_from_queue(word)
                    return False
            else:
                logging.info('Wort wurde bei OPTV vor dem Protokolldatum gefunden.')
                delete_from_queue(word)
                return False
        else:
            logging.info("Key does not exist. Key: " + str(key))
            return False
    
    else:
        return False


"""
Alte Funktion mit Twitter
def send_word(word, keys):

    metadata = check_for_infos(word, keys)
    mastodon_id = toot_word(word, keys, metadata)
    twitter_id = tweet_word(word, keys, metadata)

    if not mastodon_id:
        logging.debug('Es wurde keine Mastodon ID gefunden.')
    if not twitter_id:
        logging.debug('Es wurde keine Tweet ID gefunden.')

    if mastodon_id or twitter_id:
        return cleanup_db(word, twitter_id, mastodon_id)
    else:
        raise Exception('Es wurde keine ID gefunden.')
"""
def send_word(word, keys):

    metadata = check_for_infos(word, keys)
    mastodon_id = toot_word(word, keys, metadata)

    if not mastodon_id:
        logging.debug('Es wurde keine Mastodon ID gefunden.')

    if mastodon_id:
        return cleanup_db(word, mastodon_id)
    else:
        raise Exception('Es wurde keine ID gefunden.')

def cleanup_db(word, mastodon_id):

    # Ins Archiv bewegen
    try:
        postRedis.move(word, 2)
        # pastRedis.hset(word, "tweet_id", twitter_id)
        pastRedis.hset(word, "mastodon_id", mastodon_id)
        delete_from_queue(word)
        logging.info('Wort wurde ins Archiv verschoben.')
        return True
    except Exception as e:
        logging.exception(e)
        return False

def set_tweet_stopper():

    expireTime = 60*round(random.randrange(55,120))
    postRedis.set('meta:tweetstop', 1 , ex=expireTime)
    logging.info('Tweet-Stopper wurde gesetzt auf ' + str(expireTime/60) + ' Minuten.')

    return True










if __name__ == "__main__":
    import os
    log_file = os.path.join(os.path.dirname(__file__), 'post.log')
    logging.basicConfig(
        filename=log_file,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')    
    post_from_queue()