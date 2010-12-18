#!/usr/bin/env python
#-*- coding:utf-8 -*-

from urllib import urlencode
from urllib2 import urlopen, Request
from simplejson import dumps, loads
from base64 import decodestring, b64encode
from StringIO import StringIO
from xmlrpclib import Server
import cyclone.web
from twisted.internet import defer
from zope.interface import implements
from nsivideoconvert.interfaces.xmlrpc import IXmlrpc
from nsi.multimedia.transform.ogg_converter import OggConverter
from nsi.multimedia.utils import replace_file_extension

class XmlrpcHandler(cyclone.web.XmlrpcRequestHandler):

    implements(IXmlrpc)
    count = 0

    def _get_current_user(self):
        auth = self.request.headers.get("Authorization")
        if auth:
          return decodestring(auth.split(" ")[-1]).split(":")

    @defer.inlineCallbacks
    def _check_auth(self):
        if not self.settings.auth.authenticate(*self._get_current_user()):
            defer.returnValue("Authorization Failed!")

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def xmlrpc_done(self, uid):
        self._check_auth()
        sam = Server("http://video:convert@localhost:8888/xmlrpc")
        video_dict = yield sam.get(uid)
        if isinstance(video_dict, str):
            video_dict = eval(video_dict)
            if isinstance(video_dict, dict) and not isinstance(video_dict.get("data"), dict):
                defer.returnValue(True)
        defer.returnValue(False)

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def xmlrpc_convert(self, video):
        self._check_auth()
        to_convert_video = {"video":video, "converted":False}
        to_convert_uid = yield self._pre_store_in_sam(to_convert_video)
        response = yield self._enqueue_uid_to_convert(to_convert_uid)
        defer.returnValue(to_convert_uid)

    def _enqueue_uid_to_convert(self, uid):
        message = {"uid":uid}
        data = urlencode({"queue":"to_convert", "value":dumps(message)})
        request = Request("http://localhost:8886/", data)
        response = urlopen(request)
        response_data = response.read()
        return response_data

    def _pre_store_in_sam(self, video):
        SAM = Server('http://video:convert@localhost:8888/xmlrpc')
        return SAM.set(video)

