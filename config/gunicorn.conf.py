import os

def numCPUs():
	if not hasattr(os, "sysconf"):
		raise RuntimeError("No sysconf detected.")
	return os.sysconf("SC_NPROCESSORS_ONLN")

bind = '127.0.0.1:8002'
#workers = numCPUs() * 2 + 1
backlog = 2048
worker_class = "sync"
debug = True
#daemon = True
proc_name = 'youtube-dl'
pidfile = '/tmp/gunicorn-youtube-dl.pid'
logfile = '/var/log/mafro/youtube-dl/gunicorn.log'
#loglevel = 'debug'

