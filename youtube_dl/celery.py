from __future__ import absolute_import

from celery import Celery

celery = Celery(broker='amqp://guest@localhost:5672//')

celery.conf.update(
    CELERY_DEFAULT_QUEUE = "youtube-dl",
    CELERY_DEFAULT_EXCHANGE = "youtube-dl",
    CELERY_DEFAULT_EXCHANGE_TYPE = "direct",
    CELERY_DEFAULT_ROUTING_KEY = "youtube-dl",
)
