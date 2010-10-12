from zope.interface import Interface

class IXmlrpc(Interface):

    def get_current_user():
        """Returns the user and password of request"""

    def xmlrpc_convert(key):
        """ """

