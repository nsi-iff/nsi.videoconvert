#!/usr/bin/env python
# encoding: utf-8
from os import remove
from os.path import exists
from base64 import decodestring, b64encode
from restfulie import Restfulie
from nsi.multimedia.transform.ogg_converter import OggConverter
from nsi.multimedia.utils import replace_file_extension
from celery.task import task
from celery.execute import send_task

class VideoException(Exception):
    pass

class VideoDownloadException(Exception):
    pass

@task
def convert_video(uid, callback_url, video_link, sam_settings):
    if video_link:
        uid = download_video_and_store_in_sam(video_link, uid, sam_settings)

    video_b64 = get_from_sam(uid, sam_settings)
    if not video_b64.data.converted:
        print "Conversion started."
        uid = process_video(uid, video_b64.data.video, "/tmp/converted", sam_settings)
        print "Conversion finished."
        if not callback_url == None:
            print "Callback task sent."
            send_task('nsivideoconvert.tasks.execute_callback', args=(callback_url, uid))
        else:
            print "No callback."
        return uid
    else:
        raise VideoException("Video already converted.")

def download_video_and_store_in_sam(video_link, uid, sam_settings):
    try:
        print "Downloading video from %s" % video_link
        video = Restfulie.at(video_link).get().body
    except Exception:
        raise VideoDownloadException("Could not download the video from %s" % video_link)
    else:
        print "Video downloaded."

    to_convert_video = {'video':b64encode(video), 'converted':False}
    downloaded_video_uid = store_in_sam(uid, to_convert_video, sam_settings)

    return downloaded_video_uid

@task(max_retries=3)
def execute_callback(url, video_uid):
    try:
        print "Sending callback to %s" % url
        response = Restfulie.at(url).as_('application/json').post(key=uid, status='Done')
    except Exception, e:
        execute_callback.retry(exc=e, countdown=10)
    else:
        print "Callback executed."
        print "Response code: %s" % response.code

def process_video(uid, video, tmp_video_path, sam_settings):
    save_video_to_filesystem(video, tmp_video_path)
    converted_video = convert_video(tmp_video_path)
    uid = store_in_sam(uid, b64encode(converted_video), sam_settings)
    return uid

def save_video_to_filesystem(video, path):
    video = decodestring(video)
    video_to_convert = open(path, 'w+')
    video_to_convert.write(video)
    video_to_convert.close()

def convert_video(path, destination=None):
    try:
        if not destination:
            destination = (path + '.ogm')
        converter = OggConverter(path, target=destination)
        converter.run()
        converted_video = open(destination or replace_file_extension(path, 'ogm')).read()
    finally:
        files_to_remove = [destination, replace_file_extension(path, 'ogm'), path]
        for file_ in files_to_remove:
            remove_if_exists(file_)
        return converted_video

def remove_if_exists(path):
    if exists(path):
        remove(path)

def store_in_sam(uid, video, sam_settings):
    sam = Restfulie.at(sam_settings['url']).auth(*sam_settings['auth']).as_('application/json')
    return sam.post(key=uid, value=video).resource().key

def get_from_sam(uid, sam_settings):
    sam = Restfulie.at(sam_settings['url']).auth(*sam_settings['auth']).as_('application/json')
    return sam.get(key=uid).resource()

