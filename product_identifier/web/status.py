from flask import Blueprint, render_template
from product_identifier.master import Master
from product_identifier.models import URL

root = Blueprint('root', __name__)
app = Master.instance()


@root.route('/', methods=['GET'])
def index():
    product_count = (app.db.session.query(URL)
                     .filter(URL.is_product == True)
                     .count())  # noqa
    total_count = (app.db.session.query(URL).count())
    return render_template('index.jinja2', product_count=product_count, total_count=total_count)


def register_routes(flask):
    flask.register_blueprint(root)
