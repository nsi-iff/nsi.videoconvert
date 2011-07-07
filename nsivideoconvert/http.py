#!/usr/bin/env python
#-*- coding:utf-8 -*-

from urllib import urlencode
from urllib2 import urlopen, Request
from json import dumps, loads
from base64 import decodestring, b64encode
from StringIO import StringIO
from xmlrpclib import Server
import cyclone.web
from twisted.internet import defer
from zope.interface import implements
from nsivideoconvert.interfaces.http import IHttp
from nsi.multimedia.transform.ogg_converter import OggConverter
from nsi.multimedia.utils import replace_file_extension
from restfulie import Restfulie
from celery.execute import send_task


class HttpHandler(cyclone.web.XmlrpcRequestHandler):

    implements(IHttp)
    count = 0

    def _get_current_user(self):
        auth = self.request.headers.get("Authorization")
        if auth:
          return decodestring(auth.split(" ")[-1]).split(":")

    def _check_auth(self):
        user, password = self._get_current_user()
        if not self.settings.auth.authenticate(user, password):
            raise cyclone.web.HTTPError(401, 'Unauthorized')

    def _load_request_as_json(self):
        return loads(self.request.body)

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def get(self):
        self._check_auth()
        self.set_header('Content-Type', 'application/json')
        uid = self._load_request_as_json().get('key')
        sam = Restfulie.at('http://localhost:8888/').auth('test', 'test').as_('application/json')
        video = yield sam.get(key=uid).resource()
        if hasattr(video.data, 'converted') and not video.data.converted:
            self.finish(cyclone.web.escape.json_encode({'done':False}))
        self.finish(cyclone.web.escape.json_encode({'done':True}))

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def post(self):
        self._check_auth()
        self.set_header('Content-Type', 'application/json')
        request_as_json = self._load_request_as_json()
        video = request_as_json.get('video')
        callback_url = request_as_json.get('callback') or None
        to_convert_video = {"video":video, "converted":False}
        to_convert_uid = yield self._pre_store_in_sam(to_convert_video)
        response = self._enqueue_uid_to_convert(to_convert_uid, callback_url)
        self.finish(cyclone.web.escape.json_encode({'key':to_convert_uid}))

    def _enqueue_uid_to_convert(self, uid, callback_url):
        send_task('nsivideoconvert.tasks.convert_video', args=(uid, callback_url))

    def _pre_store_in_sam(self, video):
        SAM = Restfulie.at('http://localhost:8888/').auth('test', 'test').as_('application/json')
        return SAM.put(value=video).resource().key

