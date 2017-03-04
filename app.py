#!/usr/bin/env python
from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
#from flask import Flask, request, jsonify, abort, make_response, json
import sys
import os
import logging
import requests
from time import sleep
#from healthcheck import HealthCheck, EnvironmentDump

try:
    import json
except ImportError:
    import simplejson as json

# version
version = '0.2.1'

# wrap the flask app and give a heathcheck url
#health = HealthCheck(app, "/healthz")
#envdump = EnvironmentDump(app, "/envz")

# Check if debug mode is required
debug = os.getenv('DEBUG', False)

# add your own data to the environment dump
#def application_data():
#    return {"maintainer": "Mitch Anderson",
#            "git_repo": "https://github.com/undeadops/inkslinger"}
#envdump.add_section("application", application_data)

class TwitterConsumer:
    def __init__(self):
        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        if debug:
            loglevel = logging.DEBUG
        else:
            loglevel = os.environ.get("LOG_LEVEL", logging.INFO)
        self.logger.setLevel(loglevel)

        needConfig = True
        while needConfig:
            self.topics_endpoint = os.getenv('TOPICS_ENDPOINT', "http://giles:5000/v1")

            self.twitter_access_key = os.getenv('TWITTER_ACCESS_KEY', False).rstrip("\n")
            self.logger.debug("twitter_access_key: %s" % self.twitter_access_key)
            self.twitter_access_secret = os.getenv('TWITTER_ACCESS_SECRET', False).rstrip("\n")
            self.logger.debug("twitter_access_secret: %s" % self.twitter_access_secret)
            self.twitter_consumer_key = os.getenv('TWITTER_CONSUMER_KEY', False).rstrip("\n")
            self.logger.debug("twitter_consumer_key: %s" % self.twitter_consumer_key)
            self.twitter_consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET', False).rstrip("\n")
            self.logger.debug("twitter_consumer_secret: %s" % self.twitter_consumer_secret)
            self.giles_endpoint = os.getenv("GILES_ENDPOINT", 'http://giles:5000/v1')
            self.logger.debug("giles_endpoint: %s" % self.giles_endpoint)

            # Fetch topics
            self.logger.info("Fetching Topics from Endpoint: %s" % self.topics_endpoint)
            num_topics = self._get_topics()
            self.logger.info("TOPICS[%s]: %s" % (num_topics,self.topics))

            err = self._check_health()
            if len(err) > 0:
                for error in err:
                    self.logger.critical("Error: %s" % error)
                sleep(15)
            else:
                needConfig = False
                self.logger.info("Configuration Checks out, Starting up....")


    def _get_topics(self):
        """
        Fetch Topics to fetch from twitter
        """
        url = "%s/topics"  % self.topics_endpoint
        try:
            r = requests.get(url)
        except:
            self.logger.info("Failed to Fetch Topics from endpoint %s" % url)
        str_topics = ""
        if r.status_code == 200:
            if r.headers['content-type'] == 'application/json':
                data = r.json()
                for topic in data['topics']:
                    if str_topics == "":
                        str_topics += str(topic)
                    else:
                        str_topics += "," + str(topic)
        self.topics = str_topics
        return len(data['topics'])


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
        headers = {"user-agent": "inkslinger/%s" % version, "Content-type": "application/json"}
        self.logger.debug("Saving Tweet....")
        self.logger.debug(tweet)
        url = "%s/%s" % (self.giles_endpoint, 'posts')
        self.logger.debug("Sending data to %s [PUT]" % url)
        r = requests.post(url, json=tweet, headers=headers)
        if r.status_code != 201:
            self.logger.info("Error Saving Tweet")
            self.logger.info("[%s] - %s" % (r.status_code, r.raise_for_status()))


    def process_tweets(self):
        """
        Process Twitter Stream API
        """
        oauth = OAuth(self.twitter_access_key, self.twitter_access_secret,
                      self.twitter_consumer_key, self.twitter_consumer_secret)
        self.logger.info("Authenticating to Twitter")
        twitter_stream = TwitterStream(auth=oauth)
        self.logger.info("Streaming from Twitter - Keywords [%s]" % self.topics)
        tweets = twitter_stream.statuses.filter(track=self.topics, language="en")

        print "Processing Tweets"
        for tweet in tweets:
            # This could be threaded to minimize delay
            self._save_mongo(tweet)
            self.logger.info("Processing Tweet")


def main():
    """
    Main Loop
    """
    tweeter = TwitterConsumer()
    tweeter.process_tweets()


if __name__ == '__main__':
    main()
