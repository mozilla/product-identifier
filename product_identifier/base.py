import os
import sys
from redis import StrictRedis
import product_identifier
from product_identifier.utils import load_config_obj

CONFIG_PATH_LOCATIONS = [
    '/etc/product_identifier',
    os.path.abspath(os.path.dirname(__file__)),
]


class ApplicationInitError(Exception):
    pass


class ApplicationUnimplementedError(Exception):
    pass


class BaseApplication(object):

    __redis = None

    @property
    def redis(self):
        return self.__redis

    def __init__(self, config=None):
        if hasattr(product_identifier, "_instance"):
            raise ApplicationInitError("cannot reinitialize application")

        for path in CONFIG_PATH_LOCATIONS:
            sys.path.append(path)

        if config is None:
            config = 'product_identifier.default_settings.DefaultConfig'
        self.config = load_config_obj(config)

        self.init()
        self.__setup_redis()
        product_identifier._instance = self

    def __setup_redis(self):
        self.__redis = StrictRedis(**self.config.REDIS)

    def init(self):
        pass

    def start(self):
        raise ApplicationUnimplementedError("Application hasn't been implemented")

    @classmethod
    def instance(cls, config=None):
        if not hasattr(product_identifier, "_instance"):
            product_identifier._instance = cls(config)

        return product_identifier._instance
