from product_identifier.master import Master


def setup_routes(flask):
    import product_identifier.web.status
    product_identifier.web.status.register_routes(flask)


def create_webapp(*args, **kwargs):
    app = Master.instance(*args, **kwargs)
    setup_routes(app.flask)
    return app.flask
