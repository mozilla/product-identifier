from product_identifier.master import Master

db = Master.instance().db


class ProductURL(db.Model):
    __tablename__ = "product_url"

    id = db.Column('id', db.Integer(), autoincrement=True, primary_key=True)
    domain = db.Column('domain', db.String(length=255), nullable=False, index=True)
    url = db.Column('url', db.Text(), nullable=False, unique=True, index=True)
    created_at = db.Column('created_at', db.DateTime(), server_default=db.func.now(), nullable=False, index=True)
