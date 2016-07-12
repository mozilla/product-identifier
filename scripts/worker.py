#!/bin/env python
from product_identifier.worker import Worker

app = Worker.instance()
app.start()