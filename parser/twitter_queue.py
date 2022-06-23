import logging
from database import twittRedis, pastRedis, r
from twitter_creds import tweet_word, toot_word
from optv_api import get_op_response
import random
from dotenv import load_dotenv
import datetime

load_dotenv()

def tweet_queue():
    
    tweetstop = twittRedis.get('meta:tweetstop')

    if tweetstop is None:
        key = twittRedis.randomkey()

        if key:
            word = twittRedis.hget(key, "word").decode("utf-8")
            id = twittRedis.hget(key, "id").decode("utf-8") 
            
            if check_open_parliament(word, id):
                if send_tweet(word,id):
                    logging.info('Tweet wurden gesendet')
                    return True
                else:
                    logging.debug('Tweet konnte nicht gesendet werden.')
                    return False
            else:
                logging.info('Wort wurde bei OPTV gefunden.')
                return False
        else:
            return False
    
    else:
        return False



def send_tweet(word, id):

    redis_id = "protokoll:" + str(id)
    keys = r.hgetall(redis_id)

    twitter_id = tweet_word(word, keys)
    mastodon_id = toot_word(word, keys)

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

def set_tweet_stopper():

    expireTime = 60*round(random.randrange(55,120))
    twittRedis.set('meta:tweetstop', 1 , ex=expireTime)
    logging.info('Tweet-Stopper wurde gesetzt.')

    return True

# Gleicht mit der externen OpenParliamentTV Datenbank ab als zweiter Check ob es nicht schon existiert.
def check_open_parliament(word, id):
    datum = r.hget('protokoll:' + str(id), 'datum').decode('UTF-8')
    
    # Datum entspricht dem Tag vor dem Protokoll
    date_to_check = datetime.datetime.strptime(datum, '%d.%m.%Y') - datetime.timedelta(days=1)
    date = date_to_check.strftime('%Y-%m-%d')
    url = 'https://de.openparliament.tv/api/v1/search/media/?q=' + word + '&date=' + date
    return get_op_response(url)













if __name__ == "__main__":
    logging.basicConfig(
        filename='twitter.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')    
    logging.info('Tweet_Skript wird gestartet')
    tweet_queue()
    logging.info('Tweet_Skript wird beendet')
