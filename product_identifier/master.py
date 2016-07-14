#from gevent import monkey
#monkey.patch_all()
import gevent
import gevent.pool
import traceback
import re
import os
import json
from furl import furl
from publicsuffixlist import PublicSuffixList
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from product_identifier.base import (
    BaseApplication,
    ApplicationInitError,
)
from product_identifier.redis_keys import (
    PROCESSED_URLS_SET,
    DOMAINS_SET,
    DB_ERRORED_URL_SET,
)
from product_identifier.utils import load_config_obj


class Master(BaseApplication):

    __flask = None

    @property
    def flask(self):
        if not self.__flask:
            raise ApplicationInitError("Cannot obtain server instance before init")
        return self.__flask

    @property
    def db(self):
        return self.__db

    def init(self, config=None):

        if config is not None:
            self.config = load_config_obj(config)

        app = Flask('product_identifier')
        app.config.from_object(self.config)
        self.__flask = app
        self.__db = SQLAlchemy(self.__flask)
        Migrate(self.__flask, self.db)

        self.handler_pool = gevent.pool.Pool(self.config.MASTER_HANDLER_POOL_SIZE)

        with open(os.path.join(self.config.DATA_DIR, "ruleset.json"), "r") as f:
            rule_set = json.load(f)
            self.product_patterns = []
            for name, pattern in rule_set["rules"].iteritems():
                self.product_patterns.append(re.compile(pattern))

        self.__psl = PublicSuffixList()

    def start(self):
        def handleURL():
            from product_identifier.models import URL
            db = Master.instance().db
            self.flask.logger.debug("JOB STARTED")
            while True:
                try:
                    # TODO: succeptible to concurrency problems
                    in_url = self.scripts.pop_zset()
                    if in_url:
                        if not self.redis.sismember(PROCESSED_URLS_SET, in_url):
                            self.flask.logger.debug("PROCESSING: {}".format(in_url))
                            uri = furl(in_url)
                            domain = self.__psl.suffix(uri.host)

                            try:
                                p = URL()
                                p.domain = domain
                                p.url = in_url
                                p.is_product = self.is_product_url(in_url)
                                db.session.add(p)
                                db.session.commit()
                            except:
                                db.session.rollback()
                                error = traceback.format_exc()
                                self.flask.logger.error("DB_ERROR: {}".format(error))
                                self.redis.sadd(DB_ERRORED_URL_SET, in_url)

                            self.redis.sadd(PROCESSED_URLS_SET, in_url)

                            self.redis.rpush(domain, in_url)
                            domain_added = self.redis.sadd(DOMAINS_SET, domain)
                            if domain_added:
                                self.flask.logger.info("ADDED DOMAIN: {}".format(domain))
                        else:
                            self.flask.logger.debug("SKIPPING: {}".format(in_url))
                    else:
                        # no results, sleep
                        gevent.sleep(1)
                except:
                    error = traceback.format_exc()
                    self.flask.logger.error("ERROR: {}".format(error))

        for i in range(self.config.MASTER_HANDLER_POOL_SIZE):
            self.handler_pool.spawn(handleURL)

    def is_product_url(self, url):
        print url
        return any([pat.match(url) for pat in self.product_patterns])
