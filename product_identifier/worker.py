from lxml import html
from urlparse import urlparse
import random
import grequests
import redis_keys
import gevent

from product_identifier.base import (
    BaseApplication,
    ApplicationInitError,
)
from product_identifier.utils import load_config_obj

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

class Worker(BaseApplication):

    domains = []
    lastDomainIndex = 0

    def init(self, config=None):
        pass

    def start(self):
        self.domains = list(self.getDomains())
        print "domains"
        print self.domains
        if not self.domains:
            print "Error, no domains"
            return
        self.loop()

    def loop(self):
        threads = [gevent.spawn(self.crawlNewDomain) for i in xrange(10)]
        gevent.joinall(threads)

    def getDomains(self):
        response = self.redis.smembers(redis_keys.DOMAINS_SET)
        return response

    def crawlNewDomain(self):
        while True:
            urlToCrawl = None
            domainsChecked = 0
            while urlToCrawl == None and domainsChecked < len(self.domains):
                print "waiting for url to crawl"
                print self.domains[self.lastDomainIndex]
                urlToCrawl = self.redis.lpop(self.domains[self.lastDomainIndex])
                self.lastDomainIndex = (self.lastDomainIndex+1)%len(self.domains)
                domainsChecked += 1
            if urlToCrawl is not None:
                self.crawlURL(urlToCrawl)
            print "sleep"
            gevent.sleep(1)

    def sendURLs(self, urls):
        self.redis.lpush(redis_keys.URLS_TO_PROCESS_LIST, *urls)

    def done_loading(self, res, **kwargs):
        url = res.url
        urlparsed = urlparse(url)
        tree = html.fromstring(res.content)
        tree.make_links_absolute(base_url=url)
        links = []
        for i in tree.iterlinks():
            crawled_url = urlparse(i[2])
            if crawled_url.path.endswith('.css') or crawled_url.path.endswith('.jpg') or crawled_url.path.endswith(
                    '.pdf') or crawled_url.path.endswith('.js') or crawled_url.path.endswith(
                '.png') or crawled_url.path.endswith('.ico'):
                continue
            if (urlparsed.netloc == crawled_url.netloc):
                links.append(crawled_url.geturl())
        self.sendURLs(links)

    def crawlURL(self, url):
        headers = {
            'User-Agent': random.choice(UserAgents)
        }
        req = grequests.get(url, headers=headers, hooks=dict(response=self.done_loading))
        job = grequests.send(req, grequests.Pool(1))
