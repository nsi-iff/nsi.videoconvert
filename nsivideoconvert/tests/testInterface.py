import unittest
from nsivideoconvert.interfaces.auth import IAuth
from nsivideoconvert.interfaces.xmlrpc import IXmlrpc
from nsivideoconvert.auth import Authentication
from nsivideoconvert.xmlrpc import XmlrpcHandler

class TestInterface(unittest.TestCase):

    def test_auth(self):
        self.assertEquals(IAuth.implementedBy(Authentication), True)
        self.assertEquals(sorted(IAuth.names()), ['add_user',
                                                'authenticate',
                                                'del_user'])

    def test_handler(self):
        self.assertEquals(IXmlrpc.implementedBy(XmlrpcHandler), True)
        self.assertEquals(sorted(IXmlrpc.names()), ['get_current_user',
                                                'xmlrpc_convert',])

if __name__ == "__main__":
    unittest.main()

