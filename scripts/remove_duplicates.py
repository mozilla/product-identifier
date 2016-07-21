#!/usr/bin/env python
import sys
from scrapy.utils.url import canonicalize_url
import unicodecsv as csv
from product_identifier.master import Master
from product_identifier.models import URL

url_set = set()
delete_count = 0
iteration_count = 0

app = Master.instance()
db = app.db

total_urls = db.session.query(URL).count()
total_product_urls = db.session.query(URL).filter(URL.is_product == True).count()  # noqa
deleted_log = open('deleted.csv', 'a')
deleted_csv = csv.writer(deleted_log, delimiter=',')

offset = 0
QUERY_BATCH_SIZE = 10000


def get_duplicates(url_objs):
    global url_set
    global delete_count
    delete_ids_set = set()

    for obj in url_objs:
        canonical_url = canonicalize_url(obj.url)

        if canonical_url in url_set:
            delete_count += 1
            delete_ids_set.add(obj.id)
            deleted_csv.writerow([obj.id, obj.domain, obj.url, obj.is_product])
        else:
            url_set.add(canonical_url)
    return list(delete_ids_set)


def delete_ids(ids):
    q = URL.__table__.delete(URL.__table__.c.id.in_(ids))
    db.session.execute(q)
    db.session.commit()

while offset < total_urls:
    iteration_count += 1
    urls = db.session.query(URL).order_by(URL.id).offset(offset).limit(QUERY_BATCH_SIZE).all()
    dupes = get_duplicates(urls)
    delete_ids(dupes)
    sys.stdout.write("iter: {} processed: {}/{} delete_count: {}\r".format(iteration_count, offset, total_urls, delete_count))
    sys.stdout.flush()
    offset += QUERY_BATCH_SIZE
print "\n"
