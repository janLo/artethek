import arte
import models
import database
from multiprocessing.pool import ThreadPool
import threading
import os


fake_progress = {}


def get_progress(video):
    """Get the progress of a video downloading.

    :type video: models.Video
    :param video: The video instance.
    :rtype: float
    :return: The progress in percent
    """
    if video.state in ["CONVERTING", "COMPLETE", "FAIL"]:
        return 100.0
    if video.state in ["NEW"]:
        return 0.0
    if video.id not in fake_progress:
        return 0.0
    else:
        return fake_progress[video.id]


def download_video(video):
    """Trigger a video download.

    :type video: models.Video
    :param video: The video instance.
    :return:
    """
    _do_download_video(video.id, video.rtmp)


pool = ThreadPool(3)
progress_update_lock = threading.RLock()

def _do_download_video(video_id, video_url):
    """Do really download and convert the video.

    This indirect calling is to easier replace the implementation
    details. It should offload the downloading to any async worker
    (e.g. a ThreadPool or a uwsgi spooler/mule).

    It has to update the progress of the download. For this also
    the get_progress() method has to be changed if another method
    will be used.

    :type video_id: int
    :param video_id: The id of the video in the database.
    :type video_url: basestring
    :param video_url: The rtmp url of the video.
    """

    flv_target_path = arte.flv_path(video_id)
    mp4_target_path = arte.mp4_path(video_id)

    def work():
        with progress_update_lock:
            fake_progress[video_id] = 0.0
        video = database.db_session.query(models.Video).get(video_id)
        try:
            video.state = "LOADING"
            database.db_session.commit()
            for progress in arte.rtmp_download_progress(video_url, flv_target_path):
                with progress_update_lock:
                    fake_progress[video_id] = progress
            video.state = "CONVERTING"
            database.db_session.commit()
            arte.convert_video_container(flv_target_path, mp4_target_path)
            video.state = "COMPLETE"
            database.db_session.commit()
        except Exception as ex:
            import traceback
            traceback.print_exc()
            video.state = "FAIL"
            database.db_session.commit()


    pool.apply_async(work)

