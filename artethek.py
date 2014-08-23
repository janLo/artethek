from flask import Flask, render_template, request, jsonify, abort, send_file, make_response, request
from werkzeug import wsgi

import arte
from helper import json_view, json_fail, json_ok, make_simple_json_response
from database import db_session, init_db
import models
import worker
import os


app = Flask(__name__)


@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def start():
    return render_template("start.html")


@app.route('/lookup', methods=["POST"])
@json_view
def lookup_video():
    url = request.form.get("video_url")
    if url is None:
        return json_fail(u"No URL found")

    lang_switch = arte.LanguageSwitch.from_video_url(url)
    if lang_switch is None:
        return json_fail(u"cannot load language switch")

    quality_switch = lang_switch.get_quality_switch()
    if quality_switch is None:
        return json_fail(u"cannot load quality switch")

    return json_ok({"languages": lang_switch.get_languages(),
                    "qualities": quality_switch.get_qualities()})



@app.route("/enqueue", methods=["POST"])
@json_view
def enqueue_video():
    url = request.form.get("video_url")
    lang = request.form.get("video_lang")
    quality = request.form.get("video_quality")

    if url is None or lang is None or quality is None:
        return json_fail("Scrambled post data")

#    if db_session.query(models.Video).filter_by(url=url).count() > 0:
#        return json_fail(u"Video already enqueued")

    try:
        lang_switch = arte.LanguageSwitch.from_video_url(url)
        if lang_switch is None:
            return json_fail(u"cannot load language switch")

        quality_switch = lang_switch.get_quality_switch(lang=lang)
        if quality_switch is None:
            return json_fail(u"cannot load quality switch")

        rtmp = quality_switch.get_video_url(quality)
        if rtmp is None:
            return json_fail(u"Cannot fetch rtmp url")
    except Exception as ex:
        return json_fail("Exception caught: %s" % ex.message)

    video = models.Video(name=quality_switch.name,
                         url=url,
                         thumbnail=quality_switch.thumbnail,
                         date=quality_switch.date,
                         quality=quality,
                         lang=lang,
                         rtmp=rtmp)

    db_session.add(video)
    db_session.commit()
    # ToDo make downloading here
    worker.download_video(video)

    return json_ok({"video": video.json_repr()})


@app.route("/video", methods=["POST"])
@json_view
def video_info():
    video_id = request.form.get("video_id")
    if video_id is None:
        return json_fail("No Videoid given")
    video = None
    try:
        video = db_session.query(models.Video).get(int(video_id))
    except:
        pass
    if video is None:
        return json_fail("Video not found")

    progress = worker.get_progress(video)

#    if video.state == "NEW":
#        video.state = "LOADING"

#    if video.state == "CONVERTING":
#        video.state = "COMPLETE"
#    if progress >= 100 and video.state == "LOADING":
#        video.state = "CONVERTING"


#    db_session.commit()

    return json_ok({"video": video.json_repr(), "progress": progress})

@app.route("/videos")
def videos():
    qry = db_session.query(models.Video)
    data = [video.json_repr() for video in qry]
    return make_simple_json_response(data)


@app.route("/delete/", defaults={"video_id": -1})
@app.route("/delete/<int:video_id>", methods=["DELETE"])
def video_delete(video_id):
    video = None
    try:
        video = db_session.query(models.Video).get(int(video_id))
    except:
        pass
    if video is None:
        abort(404)

    db_session.delete(video)
    db_session.commit()
    return "", 200



@app.route("/download/", defaults={"video_id": -1})
@app.route("/download/<int:video_id>.mp4")
def video_download(video_id):
    video = None
    try:
        video = db_session.query(models.Video).get(int(video_id))
    except:
        pass
    if video is None:
        abort(404)

    if video.state != "COMPLETE":
        abort(404)

    fname = arte.mp4_path(video.id)

    return send_file(fname, mimetype="video/mp4")



if __name__ == '__main__':
    app.debug = True
    #app.use_x_sendfile = True
    init_db()
    app.run()
