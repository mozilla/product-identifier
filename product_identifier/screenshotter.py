from gevent import monkey
monkey.patch_all()  # noqa
import os
import gevent
import hashlib
from io import BytesIO
import traceback
from PIL import Image
from selenium import webdriver
import boto
from boto.s3.key import Key
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from product_identifier.base import (
    BaseApplication,
    ApplicationInitError,
)
from product_identifier.redis_keys import SCREENSHOT_URLS_SET
from product_identifier.utils import load_config_obj


class ScreenShotter(BaseApplication):

    __flask = None

    @property
    def db(self):
        return self.__db

    @property
    def flask(self):
        if not self.__flask:
            raise ApplicationInitError("Cannot obtain server instance before init")
        return self.__flask

    def init(self, config=None):

        if config is not None:
            self.config = load_config_obj(config)

        app = Flask('product_identifier')
        app.config.from_object(self.config)
        self.__flask = app

        self.__db = SQLAlchemy(self.__flask)
        Migrate(self.__flask, self.db)

    def start(self):
        greenlets = [gevent.spawn(self.screenshot_url) for i in xrange(self.config.PHANTOM_POOL_SIZE)]
        gevent.joinall(greenlets)

    def screenshot_url(self):
        self.flask.logger.debug("SCREENSHOTTER: STARTED")
        s3 = boto.connect_s3()
        bucket = s3.get_bucket(self.config.S3_BUCKET)
        target_width = self.config.IMG_WIDTH

        from product_identifier.models import URLScreenshot
        img_headers = {'Content-Disposition': "inline", "Content-Type": "image/png"}

        while True:
            try:
                data = self.scripts.pop_zset(keys=[SCREENSHOT_URLS_SET])

                if not data:
                    gevent.sleep(1)
                    continue

                url_id, url = data.split("\t")
                url_id = int(url_id)
                url = url.decode("utf-8")

                driver = webdriver.PhantomJS(self.config.PHANTOM_PATH)
                driver.set_window_size(self.config.PHANTOM_WIDTH, self.config.PHANTOM_HEIGHT)
                driver.get(url)
                gevent.sleep(5)
                img_bytes = BytesIO(driver.get_screenshot_as_png())
                driver.close()

                img = Image.open(img_bytes).convert(mode="LA")
                factor = img.width / float(target_width)
                target_height = int(img.height / factor)
                img = img.resize((target_width, target_height))

                file_like = BytesIO()
                img.save(file_like, format="png")
                out_bytes = file_like.read()
                file_like.seek(0)

                hsh = hashlib.sha1()
                hsh.update(out_bytes)
                digest = hsh.hexdigest()

                key_name = os.path.join(self.config.S3_KEY_PREFIX, "{}.png".format(digest))
                key = Key(bucket)
                key.name = key_name
                key.set_contents_from_file(file_like, headers=img_headers)
                key.set_acl("public-read")
                img_url = key.generate_url(expires_in=0, query_auth=False)
                self.flask.logger.debug("SCREENSHOTTER: S3_OBJECT_URL {}".format(img_url))

                sshot = URLScreenshot()
                sshot.url_id = url_id
                sshot.img_url = img_url

                try:
                    self.db.session.add(sshot)
                    self.db.session.commit()
                except:
                    self.db.session.rollback()
                    raise

            except:
                error = traceback.format_exc()
                self.flask.logger.error(error)
            gevent.sleep(0.25)
