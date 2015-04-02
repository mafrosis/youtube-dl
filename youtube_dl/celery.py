from __future__ import absolute_import

from celery import Celery

app = Celery(broker='amqp://guest@localhost:5672//')

app.conf.update(
    CELERY_DEFAULT_QUEUE = "youtube-dl",
    CELERY_DEFAULT_EXCHANGE = "youtube-dl",
    CELERY_DEFAULT_EXCHANGE_TYPE = "direct",
    CELERY_DEFAULT_ROUTING_KEY = "youtube-dl",
)
