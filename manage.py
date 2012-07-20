#! /usr/bin/env python

from __future__ import absolute_import
from flask.ext.script import Manager

from youtube_dl import app
from youtube_dl.tasks import import_from_youtube

manager = Manager(app)

@manager.command
def download(url):
    import_from_youtube(url, log_to_stdout=True)

if __name__ == "__main__":
    manager.run()
