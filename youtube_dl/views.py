from flask import request, make_response

from youtube_dl import app
from youtube_dl.tasks import import_from_youtube

@app.route("/")
def index():
    url = request.args.get("url") 
    if url is not None:
        import_from_youtube.delay(url)
        return make_response("Done!")
    else:
        return make_response("No URL supplied!")
