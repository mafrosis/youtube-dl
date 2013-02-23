import json
import md5
import os
import re
import shutil
import subprocess
from subprocess import Popen, PIPE, STDOUT

from youtube_dl import celery

STORAGE_PATH = "/media/icybox/data/MP3/MP3/youtube/"


@celery.task
def import_from_youtube(url, log_to_stdout=False):
    filename = None
    lock = None

    try:
        # TODO elementary handling of a double click..
        lock = md5.new(url).hexdigest()
        if os.path.exists("/tmp/%s.lock" % lock):
            print "[WARNING] This url is already being downloaded: %s" % url
            return
        else:
            f = open("/tmp/%s.lock" % lock, "w+")
            f.write("")
            f.close()

        # download stream
        print "[INFO] Downloading %s" % url
        proc = Popen(
            "/usr/local/bin/youtube-dl --write-info-json --no-progress %s" % url,
            stdout=PIPE,
            stderr=STDOUT,
            shell=True,
            cwd="/tmp"
        )
        output, stderr = proc.communicate()

        output = output.split("\n")
        for line in output:
            if line.startswith("[download] Destination: "):
                filename = line[24:39]
                break
            elif line.endswith("has already been downloaded"):
                filename = line[11:26]
                print "[INFO] Already downloaded /tmp/%s" % filename
                break

        if filename is None:
            # download failed somehow
            raise Exception("Failed parsing out filename")

        print "[INFO] Processing %s" % filename

        # parse the info file for tagging
        f = open("/tmp/%s.info.json" % filename, "r")
        info = json.loads(f.read())
        f.close()

        # use the movie's meta title as the mp3 filename
        outputname = "%s.mp3" % re.sub("[^a-zA-Z0-9]", "_", info['stitle'])

        if os.path.splitext(filename)[1] != "mp3":
            # convert to MP3
            print "[INFO] Converting to mp3"
            subprocess.check_call('/usr/bin/ffmpeg -i "/tmp/%s" -loglevel panic -y -vn -acodec libmp3lame -ar 44100 -ac 2 "/tmp/%s"' % (filename, outputname), shell=True)
        else:
            # rename the file
            os.rename(filename, outputname)

        # elementary tagging
        print "[INFO] Tagging %s" % outputname
        subprocess.check_call("/usr/bin/eyeD3 --no-color -a '%s' -t '%s' -A 'Youtube-DL' --set-user-text-frame 'Ripping Tool:youtube-dl' --set-url-frame 'WOAF:%s' /tmp/%s" % (info['title'],info['title'], url, outputname), shell=True)

        # move the new file into mpd lib
        shutil.move("/tmp/%s" % outputname, "%s%s" % (STORAGE_PATH, outputname))
        print "[INFO] Copied to %s%s" % (STORAGE_PATH, outputname)

        # remove the URL lock
        os.remove("/tmp/%s.lock" % lock)

    finally:
        # clean up
        if filename is not None:
            if os.path.exists("/tmp/%s.lock" % lock):
                os.remove("/tmp/%s.lock" % lock)

            if os.path.exists("/tmp/%s" % filename):
                os.remove("/tmp/%s" % filename)

            if os.path.exists("/tmp/%s.info.json" % filename):
                os.remove("/tmp/%s.info.json" % filename)
