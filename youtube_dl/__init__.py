# setup Celery
from youtube_dl.celery import celery

# setup Flask
from flask import Flask
app = Flask(__name__)
app.debug = True

import views

if __name__ == '__main__':
    app.run()
