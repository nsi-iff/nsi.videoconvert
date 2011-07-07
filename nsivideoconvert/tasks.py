#!/usr/bin/env python
# encoding: utf-8
from base64 import decodestring, b64encode
from restfulie import Restfulie
from nsi.multimedia.transform.ogg_converter import OggConverter
from nsi.multimedia.utils import replace_file_extension
from celery.task import task

class VideoException(Exception):
    pass

@task
def convert_video(uid, callback_url):
    video_b64 = get_from_sam(uid)
    if not video_b64.data.converted:
        print "Conversion started."
        uid = process_video(uid, video_b64.data.video, "/tmp/converted")
        print "Conversion finished."
        if not callback_url == None:
            print callback_url
            response = Restfulie.at(callback_url).as_('application/json').post(key=grains_uid, status='Done')
            print "Callback executed."
            print "Response code: %s" % response.code
        else:
            print "No callback."
        return uid
    else:
        raise VideoException("Video already converted.")

def process_video(uid, video, tmp_video_path):
    save_video_to_filesystem(video, tmp_video_path)
    converted_video = convert_video(tmp_video_path)
    uid = store_in_sam(uid, b64encode(converted_video))
    return uid

def save_video_to_filesystem(video, path):
    video = decodestring(video)
    video_to_convert = open(path, 'w+')
    video_to_convert.write(video)
    video_to_convert.close()

def convert_video(path, destination=None):
    if not destination:
        destination = (path + '.ogm')
    converter = OggConverter(path, target=destination).run()
    return open(destination or replace_file_extension(path, 'ogm')).read()

def store_in_sam(uid, video):
    sam = Restfulie.at("http://0.0.0.0:8888/").as_("application/json").auth('test', 'test')
    return sam.post(key=uid, value=video)

def get_from_sam(uid):
    sam = Restfulie.at("http://0.0.0.0:8888/").as_("application/json").auth('test', 'test')
    return sam.get(key=uid).resource()

