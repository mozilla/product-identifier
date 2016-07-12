import os


class DefaultConfig(object):
    DEBUG = True
    APPLICATION_ROOT = None
    JSONIFY_PRETTYPRINT_REGULAR = True

    ENVIRONMENT = "dev"

    SECRET_KEY = "moz-product-identifier-development-key"

    TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

    SQLALCHEMY_DATABASE_URI = "postgres://localhost/moz_productid"
    SQLALCHEMY_TRACK_MODIFICATIONS = None
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_POOL_TIMEOUT = 10
