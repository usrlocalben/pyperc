#!/usr/bin/env python2.7

import time
import json
import ujson
import pprint
import urlparse

import twisted.internet.reactor
import twisted.web.server
import twisted.web.resource

import pyperc

PERC_POLL_PERIOD = 1

def limited_to(limit, iterable):
    total = 0
    for item in iterable:
        if total >= limit:
            return
        yield item
        total += 1

class percapi(twisted.web.resource.Resource):
    isLeaf = True
    request_count = 0

    def render_GET(self, request):

        remote_host = request.getHost() #( twisted.internet.address.IPv4Address .host, .port, .type )
        print "%s %s" % (remote_host.host, request.uri)

        #up = urlparse.urlparse(request.uri)
        #qd = urlparse.parse_qs(up.query)
        args = {k:v[0] for k,v in urlparse.parse_qs(urlparse.urlparse(request.uri).query).iteritems()}

        self.request_count += 1
        request.setHeader("Content-type", "application/json")

        if request.path == '/info/':
            return ujson.dumps({
                'success': True,
                'ad': pa.adinfo,
                'cf': pa.cfinfo,
                'ld': pa.ldinfo,
                'pd': pa.pdinfo,
                'pd_to_ld': pa.pd_to_ld,
            })

        elif request.path == '/events/':
            since = args.get('since', None)
            limit = args.get('limit', None)

            if since:
                print 'filtering by id'
                events = takewhile(lambda item: item['id'] > since, pa.events)
            else:
                print 'results are unfiltered'
                events = pa.events

            if limit:
                print 'limiting to ', limit
                events = limited_to(limit, events)
            else:
                print 'results are unlimited'

            return ujson.dumps({
                'success': True,
                'events': list(events),
            })

        else:
            print 'bad request: ['+request.path+']'
            return ujson.dumps({'success':False,'message':'unknown request'})


def percpoll(s):
    pa.refresh()
    twisted.internet.reactor.callLater(PERC_POLL_PERIOD,percpoll,"again")


pa = pyperc.perc()


twisted.internet.reactor.callLater(0,percpoll,"first")

twisted.internet.reactor.listenTCP(50001, twisted.web.server.Site(percapi()))

twisted.internet.reactor.run()

