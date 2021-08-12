from database import twittRedis as r
from twitter_creds import tweet_word
import random
from datetime import datetime, time
import pytz
from sentry_sdk import capture_message



def is_time_between(begin_time, end_time):
    tz = pytz.timezone('Europe/Berlin')
    berlin_now = datetime.now(tz).time()

    # If check time is not given, default to current UTC time
    if begin_time < end_time:
        return berlin_now >= begin_time and berlin_now <= end_time
    else: # crosses midnight
        return berlin_now >= begin_time or berlin_now <= end_time


def add_to_queue(word, sitzung, url):

    print(word)

    r.hset(word, "word", word)
    r.hset(word, "sitzung", sitzung)
    r.hset(word, "url", url)

    return True


def tweet_queue():
    
    tweetstop = r.get('meta:tweetstop')

    if tweetstop is None:
        key = r.randomkey()
        word = r.hget(key, "word").decode("utf-8") 
        sitzung = r.hget(key, "sitzung").decode("utf-8") 
        url = r.hget(key, "url").decode("utf-8") 

        expireTime = 60*round(random.randrange(0,30))

        if tweet_word(word, sitzung, url):
            r.set('meta:tweetstop', 1 , ex=expireTime)
            r.delete(key)

            return True










if __name__ == "__main__":
    tweet_queue()