# Load initial urls in the to-process list
#
# import initial_loader
# ....
# initial_loader.load_initial_sites(self.redis)

import json
import redis_keys

def load_initial_sites(redis):
    f = open('product_identifier/data/sites_to_crawl.json', 'r')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    sites = parsed_json['sites']
    redis.lpush(redis_keys.URLS_TO_PROCESS_LIST, *sites)