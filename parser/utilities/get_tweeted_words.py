#!/usr/bin/env python
# encoding: utf-8

import tweepy
from database import r, pastRedis
from dotenv import load_dotenv
import os

load_dotenv()



#Twitter API credentials
consumer_key=os.environ.get('FIRST_CONSUMER_KEY')
consumer_secret=os.environ.get('FIRST_CONSUMER_SECRET')
access_key=os.environ.get('FIRST_ACCESS_TOKEN_KEY')
access_secret=os.environ.get('FIRST_ACCESS_TOKEN_SECRET')


def get_all_tweets(screen_name):
    #Twitter only allows access to a users most recent 3240 tweets with this method
    
    #authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

    api = tweepy.API(auth)

    
    #initialize a list to hold all the tweepy Tweets
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name,count=200)
    
    #save most recent tweets
    alltweets.extend(new_tweets)
    
    #save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1
    
    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        print(f"getting tweets before {oldest}")
        
        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name = screen_name,count=200,max_id=oldest)
        
        #save most recent tweets
        alltweets.extend(new_tweets)
        
        #update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
        
        print(f"...{len(alltweets)} tweets downloaded so far")
    
    
    for tweet in alltweets:
        r.hset('word:' + tweet.text, 'word', tweet.text)
        r.hset('word:' + tweet.text, 'id', tweet.id)
        pastRedis.hset('word:' + tweet.text, 'word', tweet.text)
        pastRedis.hset('word:' + tweet.text, 'id', tweet.id)
    pass


if __name__ == '__main__':
	#pass in the username of the account you want to download
	get_all_tweets("First_Said_BT")

  



