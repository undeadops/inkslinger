#!/usr/bin/env python
from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
import sys
import os
import logging
import requests
from time import sleep

try:
    import json
except ImportError:
    import simplejson as json


class TwitterConsumer:
    def __init__(self):
        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        loglevel = os.getenv('LOG_LEVEL', 'info')

        self.logger.setLevel(logging.DEBUG)

        needConfig = True
        while needConfig:
            #self.topics = 'docker,devops,#F1,coreos,#AWS,@Docker,@awscloud,@LewisHamilton'
            self.topics = os.getenv('TOPICS', False)
            self.logger.debug("TOPICS: %s" % self.topics)
            self.twitter_access_key = os.getenv('TWITTER_ACCESS_KEY', False)
            self.logger.debug("twitter_access_key: %s" % self.twitter_access_key)
            self.twitter_access_secret = os.getenv('TWITTER_ACCESS_SECRET', False)
            self.logger.debug("twitter_access_secret: %s" % self.twitter_access_secret)
            self.twitter_consumer_key = os.getenv('TWITTER_CONSUMER_KEY', False)
            self.logger.debug("twitter_consumer_key: %s" % self.twitter_consumer_key)
            self.twitter_consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET', False)
            self.logger.debug("twitter_consumer_secret: %s" % self.twitter_consumer_secret)
            self.giles_endpoint = os.getenv("GILES_ENDPOINT", 'http://giles/v1/')
            self.logger.debug("giles_endpoint: %s" % self.giles_endpoint)
            err = self._check_health()
            if len(err) > 0:
                for error in err:
                    self.logger.critical("Error: %s" % error)
                sleep(15)
            else:
                needConfig = False
                self.logger.info("Configuration Checks out, Starting up....")


    def _check_health(self):
        """
        Application health check
        Report Missing Settings to logger
        """
        err = []
        if not self.twitter_access_key:
            err.append("Missing twitter_access_key")
        if not self.twitter_access_secret:
            err.append("Missing twitter_access_secret")
        if not self.twitter_consumer_key:
            err.append("Missing twitter_consumer_key")
        if not self.twitter_consumer_secret:
            err.append("Missing twitter_consumer_secret")
        return err


    def _save_mongo(self, tweet):
        """
        Save Tweet to MongoDB via Giles API
        """
        headers = {'user-agent': 'inkslinger/0.0.1', "`Content-type": "application/json"}
        self.logger.debug("Saving Tweet....")
        self.logger.debug(tweet)
        url = "%s/%s" % (self.giles_endpoint, 'posts')
        self.logger.debug("Sending data to %s [PUT]" % url)
        r = requests.post(url, json=tweet, headers=headers)
        if r.status_code == 200 or r.status_code == 201:
            return True
        else:
            self.logger.info("Error Saving Tweet")
            self.logger.info("[%s] - %s" % (r.status_code, r.raise_for_status()))
            return False


    def process_tweets(self):
        """
        Process Twitter Stream API
        """
        # This could be multi-threaded?
        oauth = OAuth(self.twitter_access_key, self.twitter_access_secret,
                      self.twitter_consumer_key, self.twitter_consumer_secret)
        self.logger.info("Authenticating to Twitter")
        twitter_stream = TwitterStream(auth=oauth)
        self.logger.info("Streaming from Twitter - Keywords [%s]" % self.topics)
        tweets = twitter_stream.statuses.filter(track=self.topics, language="en")

        print "Processing Tweets"
        for tweet in tweets:
            while self._save_mongo(tweet):
                self.logger.info("Processing Tweet")



def main():
    """
    Main Loop
    """
    tweeter = TwitterConsumer()
    tweeter.process_tweets()


if __name__ == '__main__':
    main()
