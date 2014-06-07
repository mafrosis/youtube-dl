from __future__ import absolute_import

import json
import md5
import os
import re
import shutil
import subprocess
import traceback
from subprocess import Popen, PIPE, STDOUT

from youtube_dl import celery

STORAGE_PATH = '/media/icybox/data/MP3/MP3/youtube/'


@celery.task
def import_from_youtube(url, log_to_stdout=False):
    filename = None
    lock = None
    output, stderr = None, None

    try:
        # TODO elementary handling of a double click..
        lock = md5.new(url).hexdigest()
        if os.path.exists('/tmp/{}.lock'.format(lock)):
            print '[WARNING] This url is already being downloaded: {}'.format(url)
            return
        else:
            with open('/tmp/{}.lock'.format(lock), 'w') as f:
                f.write('')

        # download stream
        print '[INFO] Downloading {}'.format(url)
        proc = Popen(
            'youtube-dl --write-info-json --no-progress --socket-timeout 10 {}'.format(url),
            stdout=PIPE,
            stderr=STDOUT,
            shell=True,
            cwd='/tmp'
        )
        output, stderr = proc.communicate()

        if proc.returncode != 0:
            raise DownloadError(stderr)

        for line in output.splitlines():
            if line.startswith('[download] Destination: '):
                filename = line[24:39]
                break
            elif line.endswith('has already been downloaded'):
                filename = line[11:-28]
                print '[INFO] Already downloaded /tmp/{}'.format(filename)
                break

        if filename is None:
            # download failed somehow
            raise AppError('Failed parsing out filename {}'.format(url))

        print '[INFO] Processing {}'.format(filename)

        # parse the info file for tagging
        with open('/tmp/{}.info.json'.format(filename), 'r') as f:
            info = json.loads(f.read())

        # use the movie's meta title as the mp3 filename
        outputname = '{}.mp3'.format(re.sub('[^a-zA-Z0-9]', '_', info['stitle']))

        if os.path.splitext(filename)[1] != 'mp3':
            # convert to MP3
            print '[INFO] Converting to mp3'
            subprocess.check_call(
                "/usr/bin/ffmpeg -i '/tmp/{}' -loglevel panic -y -vn -acodec libmp3lame -ar 44100 -ac 2 '/tmp/{}'".format(
                    filename, outputname
                ), shell=True
            )
        else:
            # rename the file
            os.rename(filename, outputname)

        # elementary tagging
        print '[INFO] Tagging {}'.format(outputname)
        subprocess.check_call(
            (
                "/usr/bin/eyeD3 --no-color -a '{}' -t '{}' -A 'Youtube-DL' "
                "--set-user-text-frame 'Ripping Tool:youtube-dl' "
                "--set-url-frame 'WOAF:{}' /tmp/{}"
            ).format(
                info['title'], info['title'], url, outputname
            ), shell=True
        )

        # move the new file into mpd lib
        shutil.move('/tmp/{}'.format(outputname), '{}{}'.format(STORAGE_PATH, outputname))
        print '[INFO] Copied to {}{}'.format(STORAGE_PATH, outputname)

        # remove the URL lock
        os.remove('/tmp/{}.lock'.format(lock))

    except AppError as e:
        print '[ERROR] {}'.format(e)

    except DownloadError as e:
        print '[ERROR] Youtube-dl returned non-zero status\n  {}'.format(e)

    except Exception as e:
        traceback.print_exc()
        print '[STDOUT] {}'.format(output)
        print '[STDERR] {}'.format(stderr)

    finally:
        # clean up
        if filename is not None:
            if os.path.exists('/tmp/{}'.format(filename)):
                os.remove('/tmp/{}'.format(filename))

        if os.path.exists('/tmp/{}.lock'.format(lock)):
            os.remove('/tmp/{}.lock'.format(lock))

        if os.path.exists('/tmp/{}.info.json'.format(filename)):
            os.remove('/tmp/{}.info.json'.format(filename))


class AppError(Exception):
    pass

class DownloadError(Exception):
    pass
