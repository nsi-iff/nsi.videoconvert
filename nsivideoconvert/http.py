#!/usr/bin/env python
#-*- coding:utf-8 -*-

from json import dumps, loads
from base64 import decodestring, b64encode
import functools

import cyclone.web
from twisted.internet import defer
from zope.interface import implements
from nsivideoconvert.interfaces.http import IHttp
from restfulie import Restfulie
from celery.execute import send_task
from twisted.python import log

def auth(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        auth_type, auth_data = self.request.headers.get("Authorization").split()
        if not auth_type == "Basic":
            raise cyclone.web.HTTPAuthenticationRequired("Basic", realm="Restricted Access")
        user, password = decodestring(auth_data).split(":")
        # authentication itself
        if not self.settings.auth.authenticate(user, password):
            raise cyclone.web.HTTPError(401, "Unauthorized")
        return method(self, *args, **kwargs)
    return wrapper


class HttpHandler(cyclone.web.RequestHandler):

    implements(IHttp)
    count = 0

    def _get_current_user(self):
        auth = self.request.headers.get("Authorization")
        if auth:
          return decodestring(auth.split(" ")[-1]).split(":")

    def _load_request_as_json(self):
        return loads(self.request.body)

    def _load_sam_config(self):
        self.sam_settings = {'url': self.settings.sam_url, 'auth': [self.settings.sam_user, self.settings.sam_pass]}

    def __init__(self, *args, **kwargs):
        cyclone.web.RequestHandler.__init__(self, *args, **kwargs)
        self._load_sam_config()
        self.sam = Restfulie.at(self.sam_settings['url']).auth(*self.sam_settings['auth']).as_('application/json')

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def get(self):
        uid = self._load_request_as_json().get('key')
        if not uid:
            log.msg("GET failed.")
            log.msg("Request didn't have a key to check.")
            raise cyclone.web.HTTPError(400, "Malformed request.")
        response = yield self.sam.get(key=uid)
        if response.code == '404':
            log.msg("GET failed!")
            log.msg("Couldn't find any value for the key: %s" % key)
            raise cyclone.web.HTTPError(404, 'Key not found in SAM.')
        elif response.code == '401':
            log.msg("GET failed!")
            log.msg("Couldn't authenticate with SAM.")
            raise cyclone.web.HTTPError(401, 'SAM user and password not match.')
        elif response.code == '500':
            log.msg("GET failed!")
            log.msg("Couldn't connecting to SAM.")
            raise cyclone.web.HTTPError(500, 'Error while connecting to SAM.')
        video = response.resource()
        del response
        self.set_header('Content-Type', 'application/json')
        if hasattr(video.data, 'converted') and not video.data.converted:
            del video
            log.msg('The video with key %s is done.' % uid)
            self.finish(cyclone.web.escape.json_encode({'done':False}))
        else:
            del video
            log.msg('The video with key %s is not done.' % uid)
            self.finish(cyclone.web.escape.json_encode({'done':True}))

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def post(self):
        request_as_json = self._load_request_as_json()
        callback_url = request_as_json.get('callback') or None
        video_link = None

        if not request_as_json.get('video_link'):
            video = request_as_json.get('video')
            to_convert_video = {"video":video, "converted":False}
            to_convert_uid = yield self._pre_store_in_sam(to_convert_video)
            log.msg("Video sent to granulation queue.")
        elif request_as_json.get('video_link'):
            to_convert_uid = yield self._pre_store_in_sam({"video":"", "converted":False})
            video_link = request_as_json.get('video_link')
            log.msg("Video in link %s sent to the granulation queue." % video_link)
        else:
            log.msg("POST failed.")
            log.msg("Couldn't find a video or a link to download it.")
            raise cyclone.web.HTTPError(400, 'Malformed request.')

        response = self._enqueue_uid_to_convert(to_convert_uid, callback_url, video_link)
        self.set_header('Content-Type', 'application/json')
        log.msg("Video key: %s" % to_convert_uid)
        self.finish(cyclone.web.escape.json_encode({'key':to_convert_uid}))

    def _enqueue_uid_to_convert(self, uid, callback_url, video_link):
        try:
            send_task('nsivideoconvert.tasks.VideoConversion', args=(uid, callback_url, video_link, self.sam_settings),
                      queue='convert', routing_key='convert')
        except:
            log.msg("POST failed.")
            log.msg("Couldn't put the job in the queue.")
            raise cyclone.web.HTTPError(503, "Queue service unavailable.")

    def _pre_store_in_sam(self, video):
        response =  self.sam.put(value=video)
        if response.code == '401':
            log.msg("GET failed!")
            log.msg("Couldn't authenticate with SAM.")
            raise cyclone.web.HTTPError(401, 'SAM user and password not match.')
        elif response.code == '500':
            log.msg("GET failed!")
            log.msg("Couldn't connecting to SAM.")
            raise cyclone.web.HTTPError(500, 'Error while connecting to SAM.')
        return response.resource().key

