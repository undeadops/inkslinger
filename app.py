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
    def __init__(self, topics):
        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.WARNING)
        self.topics = topics

        needConfig = True
        while needConfig:
            #self.topics = 'docker,devops,#F1,coreos,#AWS,@Docker,@awscloud,@LewisHamilton'
            self.consul_uri = os.env('CONSUL_URI', 'localhost:8500')
            self.twitter_access_token = self.consul_get('apps/inkslinger/twitter_access_token').json()
            self.logger.debug("twitter_access_token: %s" % self.twitter_access_token)
            self.twitter_access_secret = self.consul_get('apps/inkslinger/twitter_access_secret').json()
            self.logger.debug("twitter_access_secret: %s" % self.twitter_access_secret)
            self.twitter_consumer_key = self.consul_get('apps/inkslinger/twitter_consumer_key').json()
            self.logger.debug("twitter_consumer_key: %s" % self.twitter_consumer_key)
            self.twitter_consumer_secret = self.consul_get('apps/inkslinger/twitter_consumer_secret').json()
            self.logger.debug("twitter_consumer_secret: %s" % self.twitter_consumer_secret)
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
        if self.twitter_access_token == '':
            err.append("Missing twitter_access_token")
        if self.twitter_access_secret == '':
            err.append("Missing twitter_access_secret")
        if self.twitter_consumer_key == '':
            err.append("Missing twitter_consumer_key")
        if self.twitter_consumer_secret == '':
            err.append("Missing twitter_consumer_secret")
        return err

    def giles_get(self, resource, payload=None):
        """ Perform HTTP GET request against a giles endpoint """
        # Keeping with service discovery, ask consul for giles endpoint
        # maybe some kind of wait-lock here?  incase no active giles endpoints?
        giles_endpoints = self.consul_get('service/giles').json()
        self.logger.debug("giles_endpoints: %s" % giles_endpoints)
        self.logger.debug("len(giles_endpoints): %s" % len(giles_endpoints))
        payload = payload or {}
        endpoint = '{}/{}/{}'.format(, 'v1', resource)
        result = requests.get(
            endpoint,
            params=payload,
            headers={'Accept': 'application/json; version=1'})


    def consul_get(self, resource, payload=None):
        """ Perform HTTP GET request against consul endpoint """
        payload = payload or {}
        endpoint = '{}/{}/{}'.format(self.consul_uri, 'v1', resource)
        self.logger.debug("Consule: GET %s" % endpoint)
        return requests.get(
            endpoint,
            params=payload,
            headers={'Accept': 'application/vnd.consul+json; version=1'})


    def process_tweets(self):
        """
        Process Twitter Stream API
        """
        # This could be multi-threaded?
        oauth = OAuth(self.twitter_access_token, self.twitter_access_secret,
                      self.twitter_consumer_key, self.twitter_consumer_secret)
        self.logger.info("Authenticating to Twitter")
        twitter_stream = TwitterStream(auth=oauth)
        self.logger.info("Streaming from Twitter - Keywords [%s]" % self.topics)
        tweets = twitter_stream.statuses.filter(track=self.topics, language="en")

        print "Processing Tweets"
        for tweet in tweets:
            self.logger.info("Processing Tweet")


def main():
    """
    Main Loop
    """
    tweeter = TwitterConsumer()
    tweeter.process_tweets()


if __name__ == '__main__':
    main()
