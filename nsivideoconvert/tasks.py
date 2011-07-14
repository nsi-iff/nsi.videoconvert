#!/usr/bin/env python
# encoding: utf-8
from os import remove
from os.path import exists
from base64 import decodestring, b64encode
from restfulie import Restfulie
from nsi.multimedia.transform.ogg_converter import OggConverter
from nsi.multimedia.utils import replace_file_extension
from celery.task import task

class VideoException(Exception):
    pass

class VideoDownloadException(Exception):
    pass

@task
def convert_video(uid, callback_url, video_link, sam_settings):
    if video_link:
        try:
            video = Restfulie.at(video_link).get().body
        except Exception:
            raise VideoDownloadException("Could not download the video from %s" % video_link)

        sam = Restfulie.at(sam_settings['url']).auth(*sam_settings['auth']).as_('application/json')
        to_convert_video = {'video':b64encode(video), 'converted':False}
        response = sam.post(key=uid, value=to_convert_video).body
        print response

    video_b64 = get_from_sam(uid, sam_settings)
    if not video_b64.data.converted:
        print "Conversion started."
        uid = process_video(uid, video_b64.data.video, "/tmp/converted", sam_settings)
        print "Conversion finished."
        if not callback_url == None:
            print callback_url
            response = Restfulie.at(callback_url).as_('application/json').post(key=uid, status='Done')
            print "Callback executed."
            print "Response code: %s" % response.code
        else:
            print "No callback."
        return uid
    else:
        raise VideoException("Video already converted.")

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

