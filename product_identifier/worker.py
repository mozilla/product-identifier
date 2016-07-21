import os
from lxml import html
from furl import furl
import random
import grequests
import redis_keys
import gevent
from scrapy.utils.url import canonicalize_url

from product_identifier.base import (
    BaseApplication,
)

UserAgents = [
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/601.6.17 (KHTML, like Gecko) Version/9.1.1 Safari/601.6.17',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586',
    'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36']

SKIPPED_EXTENSIONS = {".css", ".jpg", ".jpeg", ".pdf", ".js", ".png", ".ico", ".oembed", ".swf", ".jpeg", ".json", ".mp4", ".gif", ".xml"}


class Worker(BaseApplication):

    def start(self):
        threads = [gevent.spawn(self.crawlNewDomain) for i in xrange(10)]
        gevent.joinall(threads)

    def getDomains(self):
        return self.redis.smembers(redis_keys.DOMAINS_SET)

    def crawlNewDomain(self):
        while True:
            urlToCrawl = None
            domains = list(self.getDomains())
            while not urlToCrawl:
                domain = random.choice(domains)
                urlToCrawl = self.scripts.get_url_for_domain(keys=[domain])
                if not urlToCrawl:
                    gevent.sleep(0.25)
            self.crawlURL(urlToCrawl)

    def sendURLs(self, urls):
        if len(urls):
            keys = [""] * len(urls)
            num_inserted = self.scripts.zset_insert_urls(keys=keys, args=urls)
            print "inserted: {}".format(num_inserted)

    def done_loading(self, res, **kwargs):
        url = res.url
        urlparsed = furl(url)
        tree = html.fromstring(res.content)
        tree.make_links_absolute(base_url=url)
        links = set()
        for i in tree.iterlinks():
            crawled_url = furl(i[2])
            _, ext = os.path.splitext(crawled_url.pathstr)
            if ext.lower() in SKIPPED_EXTENSIONS:
                continue
            if (not self.config.SAME_DOMAIN or (self.config.SAME_DOMAIN and urlparsed.netloc == crawled_url.netloc)):
                # remove url fragment
                canonical_url = canonicalize_url(crawled_url.url)
                links.add(canonical_url)
        self.sendURLs(list(links))

    def crawlURL(self, url):
        headers = {
            'User-Agent': random.choice(UserAgents)
        }
        req = grequests.get(url, headers=headers, hooks=dict(response=self.done_loading))
        grequests.send(req, grequests.Pool(1))
