# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

import asyncio
import aiocoap
import unittest
import errno

from .server import WithTestServer, WithClient, no_warnings

class TestClient(WithTestServer, WithClient):
    @no_warnings
    def test_uri_parser(self):
        yieldfrom = lambda f: self.loop.run_until_complete(f)

        request = aiocoap.Message(code=aiocoap.GET)
        request_uri = "coap://" + self.servernetloc + "/empty?query=a&query=b"
        request.set_request_uri(request_uri)
        self.assertEqual(request.get_request_uri(), request_uri, "Request URL does not round-trip in request")
        response = yieldfrom(self.client.request(request).response)
        self.assertEqual(response.get_request_uri(), request_uri, "Request URL does not round-trip in response")
        self.assertEqual(response.code, aiocoap.CONTENT, "Request URL building failed")

        request = aiocoap.Message(code=aiocoap.GET)
        request.set_request_uri("coap://" + self.servernamealias + "/empty")
        self.assertEqual(request.get_request_uri(), "coap://" + self.servernamealias + "/empty")
        response = yieldfrom(self.client.request(request).response)
        self.assertEqual(response.code, aiocoap.CONTENT, "Resolving WithTestServer.servernamealias failed")
        self.assertEqual(response.get_request_uri(), "coap://" + self.servernamealias + "/empty", "Host name did not get round-tripped")

    @no_warnings
    def test_uri_parser2(self):
        """A difficult test because it is prone to keeping the transport
        around, bothering later tests"""

        yieldfrom = lambda f: self.loop.run_until_complete(f)

        request = aiocoap.Message(code=aiocoap.GET)
        request.set_request_uri("coap://" + self.servernetloc + ":9999/empty")
        resp = self.client.request(request).response
        try:
            # give the request some time to finish getaddrinfo
            yieldfrom(asyncio.as_completed([resp], timeout=0.01).__next__())
        except OSError as e:
            self.assertEqual(e.errno, errno.ECONNREFUSED, "")
        else:
            self.fail("Request to non-opened port did not come back with 'Connection Refused'")
        self.assertEqual(request.remote.port, 9999, "Remote port was not parsed")
        resp.cancel()

    @no_warnings
    def test_uri_reconstruction(self):
        """This test aims for reconstruction of the URI when for some reasons
        the request hostname is not available. That would typically be the case
        for multicasts (where the response's URI dependes on the response
        package's origin and does not contain the multicast address), but until
        that's easily testable, this test just removes the information."""
        yieldfrom = lambda f: self.loop.run_until_complete(f)

        request = aiocoap.Message(code=aiocoap.GET)
        request_uri = "coap://" + self.servernetloc + "/empty?query=a&query=b"
        request.set_request_uri(request_uri)

        response = yieldfrom(self.client.request(request).response)
        response.requested_host = None
        response.requested_port = None
        self.assertEqual(response.get_request_uri(), request_uri, "Request URL does not round-trip in response")
        self.assertEqual(response.code, aiocoap.CONTENT, "Request URL building failed")
