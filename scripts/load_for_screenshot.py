#!/usr/bin/env python
import sys
from time import time
from product_identifier.master import Master
from product_identifier.models import URL
from product_identifier.redis_keys import SCREENSHOT_URLS_SET

iteration_count = 0

app = Master.instance()
db = app.db
redis = app.redis

total_urls = db.session.query(URL).count()
total_product_urls = db.session.query(URL).filter(URL.is_product == True).count()  # noqa

offset = 0
QUERY_BATCH_SIZE = 10000


def load_in_redis(urls):
    entries = ["{}\t{}".format(url.id, url.url.encode("utf-8")) for url in urls]
    weights = [int(time())] * len(urls)
    data = [item for pairs in zip(weights, entries) for item in pairs]
    redis.zadd(SCREENSHOT_URLS_SET, *data)

while offset < total_urls:
    iteration_count += 1
    urls = db.session.query(URL).order_by(URL.id).offset(offset).limit(QUERY_BATCH_SIZE).all()
    load_in_redis(urls)
    sys.stdout.write("iter: {} processed: {}/{}\r".format(iteration_count, offset, total_urls))
    sys.stdout.flush()
    offset += QUERY_BATCH_SIZE
print "\n"
