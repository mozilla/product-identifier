#!/usr/bin/env python
# Load initial urls in the to-process list
#
# import initial_loader
# ....
# initial_loader.load_initial_sites(self.redis)

import json
import redis_keys
import redis

REDIS = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "socket_timeout": 5,
}

def load_initial_sites(redis):
    f = open('data/sites_to_crawl.json', 'r')
    parsed_json = json.load(f)
    sites = parsed_json['sites']
    redis.lpush(redis_keys.URLS_TO_PROCESS_LIST, *sites)

conn = redis.StrictRedis(**REDIS)
load_initial_sites(conn)