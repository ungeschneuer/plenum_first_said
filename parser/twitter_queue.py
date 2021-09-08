from sentry_sdk.api import capture_exception, capture_message
from database import twittRedis, pastRedis
from twitter_creds import tweet_word
import random
import sentry_sdk
from dotenv import load_dotenv
import os 
from sentry_sdk.integrations.redis import RedisIntegration



load_dotenv()

sentry_sdk.init(
    os.environ.get('SENTRY_AUTH'),
    integrations=[RedisIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.5,
    release="plenarbot@1.1",
    environment="production"
)



def tweet_queue():
    
    tweetstop = twittRedis.get('meta:tweetstop')

    if tweetstop is None:
        key = twittRedis.randomkey()
        if key and not send_tweet(key):
            capture_message('Tweet konnte nicht gesendet werden.')
    quit()

def send_tweet(key):
    word = twittRedis.hget(key, "word").decode("utf-8")
    id = twittRedis.hget(key, "id").decode("utf-8") 


    status_id = tweet_word(word, id)

    if not status_id:
        return False
    
    return cleanup_db(word, status_id)

def cleanup_db(word, status_id):

    set_tweet_stopper()

    # Ins Archiv bewegen
    try:
        twittRedis.move(word, 2)
        pastRedis.hset(word, "tweet_id", status_id)
        return True
    except Exception as e:
        capture_exception(e)
        return False

def set_tweet_stopper():

    expireTime = 60*round(random.randrange(25,70))
    twittRedis.set('meta:tweetstop', 1 , ex=expireTime)

    return True













if __name__ == "__main__":
    tweet_queue()