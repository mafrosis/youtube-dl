from __future__ import absolute_import

from . import app

from celery import Celery

celery = Celery(broker=app.config['BROKER_URL'])
celery.config_from_object(app.config)
