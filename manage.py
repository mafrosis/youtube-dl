#! /usr/bin/env python

from __future__ import absolute_import
from flask.ext.script import Manager

from youtube_dl import app
from youtube_dl.tasks import import_from_youtube

manager = Manager(app)


@manager.command
def download(url):
    import_from_youtube(url, log_to_stdout=True)


@manager.command
def check_pip():
    import xmlrpclib
    import pip

    pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    for dist in pip.get_installed_distributions():
        available = pypi.package_releases(dist.project_name)
        if not available:
            # Try to capitalize pkg name
            available = pypi.package_releases(dist.project_name.capitalize())

        if not available:
            msg = 'no releases at pypi'
        elif available[0] != dist.version:
            msg = '{} available'.format(available[0])
        else:
            msg = 'up to date'
        pkg_info = '{dist.project_name} {dist.version}'.format(dist=dist)
        print '{pkg_info:40} {msg}'.format(pkg_info=pkg_info, msg=msg)

if __name__ == "__main__":
    manager.run()
