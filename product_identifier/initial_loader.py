#!/usr/bin/env python
# Load initial urls in the to-process list
#
# import initial_loader
# ....
# initial_loader.load_initial_sites(self.redis)

import os
import json
import redis_keys
import redis
from time import time

REDIS = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "socket_timeout": 5,
}


def load_initial_sites(redis):
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data/sites_to_crawl.json")

    f = open(fname, 'r')
    parsed_json = json.load(f)
    sites = parsed_json['sites']
    scores = [int(time()) for i in range(len(sites))]
    zipped = zip(scores, sites)
    zset_args = [item for sublist in zipped for item in sublist]
    redis.zadd(redis_keys.URLS_TO_PROCESS_SET, *zset_args)

conn = redis.StrictRedis(**REDIS)
load_initial_sites(conn)
