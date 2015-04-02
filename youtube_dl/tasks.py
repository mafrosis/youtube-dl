from __future__ import absolute_import

import json
import md5
import os
import re
import shutil
import subprocess
import traceback

from . import celery_app

DEBUG = False


@celery_app.task
def import_from_youtube(url, log_to_stdout=False):
    filename = None
    lock = None
    output, stderr = None, None

    try:
        # TODO use temp directory for each download
        # - named with hash of url (which acts as the lock)
        # - provides clean up after
        # TODO switch to python logging, with levels
        # - inherit celery's loglevel ??

        lock = md5.new(url).hexdigest()
        if os.path.exists('/tmp/{}.lock'.format(lock)):
            print '[WARNING] This url is already being downloaded: {}'.format(url)
            return
        else:
            with open('/tmp/{}.lock'.format(lock), 'w') as f:
                f.write('')

        # log youtube-dl version
        print '[INFO] youtube-dl {}'.format(subprocess.check_output('youtube-dl --version', shell=True))

        # download stream
        print '[INFO] Downloading {}'.format(url)
        proc = subprocess.Popen(
            'youtube-dl --write-info-json --no-progress --socket-timeout 10 {} 2>&1'.format(url),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            cwd='/tmp'
        )
        output, stderr = proc.communicate()

        if proc.returncode != 0:
            raise DownloadError(output)

        for line in output.splitlines():
            if DEBUG:
                print '[DEBUG] {}'.format(line)

            if line.startswith('[download] Destination: '):
                filename = line[24:]    # get the filename which is remainder of the line
                break
            #if line.startswith('[download] Destination: '):
            #    filename = line[24:39]
            #    break
            elif line.endswith('has already been downloaded'):
                filename = line[11:-28]
                print '[INFO] Already downloaded /tmp/{}'.format(filename)
                break

        if filename is None:
            # download failed somehow
            raise AppError('Failed parsing out filename {}'.format(url))

        print '[INFO] Processing {}'.format(filename)

        infok = False

        # parse the info file for tagging
        infofile = '/tmp/{}.info.json'.format(os.path.splitext(filename)[0])

        if os.path.exists(infofile) is True:
            with open(infofile, 'r') as f:
                info = json.loads(f.read())
                infok = True
        else:
            print '{} not found, no tagging today :('.format(infofile)

        # use the movie's meta title as the mp3 filename
        if infok:
            outputname = '{}.mp3'.format(re.sub('[^a-zA-Z0-9]', '_', info['stitle']))
        else:
            # default filename to youtube title
            outputname = filename
            if os.path.splitext(outputname)[1] != 'mp3':
                outputname = '{}.mp3'.format(re.sub('[^a-zA-Z0-9]', '_', outputname))

        if os.path.splitext(filename)[1] != 'mp3':
            # convert to MP3
            print '[INFO] Converting to mp3'

            ffmpeg_cmd = (
                "/usr/bin/ffmpeg -i '/tmp/{}' "
                "-loglevel panic -y -vn "
                "-acodec libmp3lame -ar 44100 -ac 2 "
                "'/tmp/{}' 2>&1"
            ).format(
                filename, outputname
            )
            if DEBUG:
                print '[DEBUG] {}'.format(ffmpeg_cmd)

            # convert it
            ffmpeg_output = subprocess.check_output(ffmpeg_cmd, shell=True)

            if DEBUG:
                print '[DEBUG] {}'.format(ffmpeg_output)
        else:
            # rename the file
            os.rename(filename, outputname)

        # elementary tagging
        if infok:
            print '[INFO] Tagging {}'.format(outputname)

            eyed3_cmd = (
                "/usr/bin/eyeD3 --no-color -a '{}' -t '{}' -A 'Youtube-DL' "
                "--set-user-text-frame 'Ripping Tool:youtube-dl' "
                "--set-url-frame 'WOAF:{}' '/tmp/{}' 2>&1"
            ).format(
                info['title'], info['title'], url, outputname
            )
            if DEBUG:
                print '[DEBUG] {}'.format(eyed3_cmd)

            # tag it
            eyed3_output = subprocess.check_output(eyed3_cmd, shell=True)

            if DEBUG:
                print '[DEBUG] {}'.format(eyed3_output)

        # move the new file into mpd lib
        subprocess.call(
            'scp /tmp/{} monopoly:/media/pools/music/mp3/youtube'.format(outputname),
            shell=True
        )
        shutil.move('/tmp/{}'.format(outputname), '/home/mafro/mp3/youtube/{}'.format(outputname))
        print '[INFO] Copied to kerplunk & monopoly'

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
