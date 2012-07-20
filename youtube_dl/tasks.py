from youtube_dl import app, celery

import os
import sys
import subprocess
import json
import logging
import shutil
import urlparse
import md5

STORAGE_PATH = "/media/icybox/data/MP3/MP3/youtube/"


@celery.task
def import_from_youtube(url, log_to_stdout=False):
    filename = None
    lock = None

    try:
        # TODO elementary handling of a double click..
        lock = md5.new(url).hexdigest()
        if os.path.exists("%s.lock" % lock):
            print "[WARNING] This url is already being downloaded: %s" % url
            return
        else:
            f = open("%s.lock" % lock, "w+")
            f.write("")
            f.close()

        # download stream
        print "[INFO] Downloading %s" % url
        output = subprocess.check_output(["youtube-dl", "--write-info-json", "--no-progress", url], stderr=subprocess.STDOUT)

        output = output.split("\n")
        for line in output:
            if line.startswith("[download]"):
                filename = line[24:]
                break

        if filename is None:
            # download failed somehow
            raise Exception("Failed parsing out filename")

        print "[INFO] Processing %s" % filename

        # parse the info file for tagging
        f = open("%s.info.json" % filename, "r")
        info = json.loads(f.read())
        f.close()

        # sort out the filename
        parts = os.path.splitext(filename)
        outputname = "%s.mp3" % info['stitle']

        if parts[1] != "mp3":
            # convert to MP3
            print "[INFO] Converting to mp3"
            subprocess.check_output(["ffmpeg", "-i", filename, "-loglevel", "panic", "-y", "-vn", "-acodec", "libmp3lame", "-ar", "44100", "-ac", "2", outputname])
        else:
            # rename the file
            os.rename(filename, outputname)

        # elementary tagging
        print "[INFO] Tagging %s" % outputname
        subprocess.check_output(["eyeD3",
                                 "--no-color",
                                 "-a", info['title'],
                                 "-t", info['title'],
                                 "-A", "Youtube-DL",
                                 "--set-user-text-frame", "Ripping Tool:youtube-dl",
                                 "--set-url-frame", "WOAF:%s" % url,
                                 outputname])

        # move the new file into mpd lib
        shutil.move(outputname, "%s%s" % (STORAGE_PATH, outputname))
        print "[INFO] Copied to %s%s" % (STORAGE_PATH, outputname)

        # remove the URL lock
        os.remove("%s.lock" % lock)

    except Exception as e:
        print "[ERROR] Failed %s" % e

        # clean up
        if os.path.exists("%s.lock" % lock):
            os.remove("%s.lock" % lock)

    finally:
        # clean up
        if filename is not None:
            if os.path.exists(filename):
                os.remove(filename)

            if os.path.exists("%s.info.json" % filename):
                os.remove("%s.info.json" % filename)
