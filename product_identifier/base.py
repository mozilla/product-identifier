import product_identifier
from product_identifier.utils import load_config_obj


class ApplicationInitError(Exception):
    pass


class ApplicationUnimplementedError(Exception):
    pass


class BaseApplication(object):

    def __init__(self, config=None):
        if hasattr(product_identifier, "_instance"):
            raise ApplicationInitError("cannot reinitialize application")

        if config is None:
            config = 'product_identifier.default_settings.DefaultConfig'
        self.config = load_config_obj(config)

        self.init()
        product_identifier._instance = self

    def init(self):
        pass

    def start(self):
        raise ApplicationUnimplementedError("Application hasn't been implemented")

    @classmethod
    def instance(cls, config=None):
        if not hasattr(product_identifier, "_instance"):
            product_identifier._instance = cls(config)

        return product_identifier._instance
