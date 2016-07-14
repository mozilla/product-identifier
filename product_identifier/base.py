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


class LuaScripts(object):
    pass


class BaseApplication(object):

    __redis = None
    __redis_scripts = None

    @property
    def redis(self):
        return self.__redis

    @property
    def scripts(self):
        return self.__redis_scripts

    def __init__(self, config=None):
        if hasattr(product_identifier, "_instance"):
            raise ApplicationInitError("cannot reinitialize application")

        for path in CONFIG_PATH_LOCATIONS:
            sys.path.append(path)

        if config is None:
            config = 'product_identifier.default_settings.DefaultConfig'
        self.config = load_config_obj(config)

        self.config.DEBUG = os.environ.get("DEBUG") if os.environ.get("DEBUG") else self.config.DEBUG
        self.config.ENVIRONMENT = os.environ.get("ENVIRONMENT") if os.environ.get("ENVIRONMENT") else self.config.ENVIRONMENT
        self.config.SECRET_KEY = os.environ.get("SECRET_KEY") if os.environ.get("SECRET_KEY") else self.config.ENVIRONMENT
        self.config.SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") if os.environ.get("SQLALCHEMY_DATABASE_URI") else self.config.SQLALCHEMY_DATABASE_URI
        self.config.REDIS['host'] = os.environ.get("REDIS_HOST") if os.environ.get("REDIS_HOST") else self.config.REDIS['host']
        self.config.REDIS['db'] = int(os.environ.get("REDIS_DB")) if os.environ.get("REDIS_DB") else self.config.REDIS['db']
        self.config.REDIS['password'] = os.environ.get("REDIS_PASSWORD") if os.environ.get("REDIS_PASSWORD") else self.config.REDIS['password']

        self.init()
        self.__setup_redis()
        self.__load_redis_scripts()
        product_identifier._instance = self

    def __setup_redis(self):
        self.__redis = StrictRedis(**self.config.REDIS)

    def __load_redis_scripts(self):
        script_obj = LuaScripts()

        fnames = [item for item in os.listdir(self.config.DATA_DIR) if item.endswith(".lua")]
        for fname in fnames:
            with open(os.path.join(self.config.DATA_DIR, fname), "r") as f:
                script = f.read()
                name, _ = os.path.splitext(fname)
                func = self.redis.register_script(script)
                setattr(script_obj, name, func)

        self.__redis_scripts = script_obj

    def init(self):
        pass

    def start(self):
        raise ApplicationUnimplementedError("Application hasn't been implemented")

    @classmethod
    def instance(cls, config=None):
        if not hasattr(product_identifier, "_instance"):
            product_identifier._instance = cls(config)

        return product_identifier._instance
