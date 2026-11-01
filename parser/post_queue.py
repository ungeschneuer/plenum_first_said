import logging
from database import (postRedis, pastRedis, r, delete_from_queue, already_posted,
                      random_queued_word, is_too_old, MAX_WORD_AGE_DAYS)
# from twitter_creds import tweet_word
from mastodon_cred import toot_word
from optv_api import double_check_newness, check_for_infos
import random
from dotenv import load_dotenv

load_dotenv()


# Organisiert das Senden von Tweets
# Bereits gepostete, zu alte oder bei OPTV schon bekannte Wörter werden entfernt.
def post_from_queue():
    
    tweetstop = postRedis.get('meta:tweetstop')

    if tweetstop is not None:
        return False

    set_tweet_stopper()
    logging.info('Tweet Skript wird gestartet')

    word = random_queued_word()

    if word is None:
        logging.info('Keine Wörter in der Queue.')
        return False

    id = postRedis.hget(word, "id")
    if id is None:
        logging.info("Wort '" + word + "' hat keine Protokoll-ID und wird entfernt.")
        delete_from_queue(word)
        return False
    id = id.decode("utf-8")

    if already_posted(word):
        logging.info("Wort '" + word + "' wurde bereits gepostet und wird aus der Queue entfernt.")
        delete_from_queue(word)
        return False

    if is_too_old(id):
        logging.info("Wort '" + word + "' stammt aus einem Protokoll älter als " + str(MAX_WORD_AGE_DAYS) + " Tage und wird entfernt.")
        delete_from_queue(word)
        return False

    logging.info("Wort '" + word + "' wird veröffentlicht.")

    redis_id = "protokoll:" + str(id)
    protokoll_keys = r.hgetall(redis_id)
    
    if double_check_newness(word, protokoll_keys):
        if send_word(word, id, protokoll_keys):
            return True
        else:
            logging.info('Wort konnte nicht gesendet werden.')
            return False
    else:
        logging.info('Wort wurde bei OPTV vor dem Protokolldatum gefunden.')
        delete_from_queue(word)
        return False


def send_word(word, id, keys):

    metadata = check_for_infos(word, keys)
    mastodon_id = toot_word(word, keys, metadata)

    if not mastodon_id:
        # Haupt-Toot ist nicht durchgegangen: Wort bleibt in der Queue für einen späteren Versuch.
        logging.info('Es wurde keine Mastodon ID gefunden.')
        return False

    return cleanup_db(word, id, mastodon_id)

def cleanup_db(word, id, mastodon_id):

    # Ins Archiv schreiben und aus der Queue entfernen.
    # Archiv zuerst, damit das Wort auch bei einem Fehler danach nicht erneut gepostet wird.
    try:
        pastRedis.hset(word, mapping={"word": word, "id": id, "mastodon_id": str(mastodon_id)})
    except Exception as e:
        logging.exception(e)
    delete_from_queue(word)
    logging.info('Wort wurde ins Archiv verschoben.')
    return True

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