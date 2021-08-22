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
    release="plenarbot@1.0",
    environment="production"
)



def tweet_queue():
    
    tweetstop = twittRedis.get('meta:tweetstop')

    if tweetstop is None:
        key = twittRedis.randomkey()
        if key:
            word = twittRedis.hget(key, "word").decode("utf-8") 
            id = twittRedis.hget(key, "id").decode("utf-8") 
 

            expireTime = 60*round(random.randrange(3,20))

            status_id = tweet_word(word, id)
            if status_id:
                sentry_sdk.capture_message("Tweet wurde gesendet.")
                twittRedis.set('meta:tweetstop', 1 , ex=expireTime)
                twittRedis.move(key['word'], pastRedis)
                pastRedis.hset(key['word'], "id", status_id)

                return True
    quit()










if __name__ == "__main__":
    tweet_queue()