import os
import sys
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from product_identifier.base import (
    BaseApplication,
    ApplicationInitError,
)
from product_identifier.utils import load_config_obj

CONFIG_PATH_LOCATIONS = [
    '/etc/product_identifier',
    os.path.abspath(os.path.dirname(__file__)),
]


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

        for path in CONFIG_PATH_LOCATIONS:
            sys.path.append(path)

        if config is not None:
            self.config = load_config_obj(config)

        app = Flask('product_identifier')
        app.config.from_object(self.config)
        self.__flask = app
        self.__db = SQLAlchemy()
        self.__db.init_app(self.__flask)
        Migrate(self.__flask, self.db)

    def start(self):
        pass
