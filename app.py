#!/usr/bin/env python
from pykafka import KafkaClient
from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
import sys
import os
import logging

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
        #self.topics = 'docker,devops,#F1,coreos,#AWS,@Docker,@awscloud,@LewisHamilton'
        self.twitter_access_token = '809943810-MesHqyhFZEBu0AjYVx4d9MyQQG1SrsE6GSOSgEP9'
        self.twitter_access_secret = 'jS0gg3ZU2UOrc4tiNoGrrzLt91wW8wmzbt9XMM8MuqNtt'
        self.twitter_consumer_key = '4PxEjeKeNJyYH27vcNBFIBKBW'
        self.twitter_consumer_secret = 'GDIreQXMCOndTiJTJeve97Vy3sXg3IbCCc7iQ42RtaPmrGb0XJ'

    def process_tweets(self):
        """
        Process Twitter Stream API
        """
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
    kafka_host = os.getenv('KAFKA_HOST', 'docker:9092')
    tweeter = TwitterConsumer(kafka_host=kafka_host)
    tweeter.process_tweets()


if __name__ == '__main__':
    main()
