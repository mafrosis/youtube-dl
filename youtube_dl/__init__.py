from __future__ import absolute_import

# setup Celery
from .celery import app as celery_app

# setup Flask
from flask import Flask
app = Flask(__name__)
app.debug = True

from . import views

if __name__ == '__main__':
    app.run()
