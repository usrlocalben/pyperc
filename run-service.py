#!/usr/bin/env python2.7

import time
import json
import ujson
import pprint
import urlparse
from itertools import takewhile

import twisted.internet.reactor
import twisted.web.server
import twisted.web.resource

from pyperc import PyPerc, MegaCLI, MegaCLIRunner


PERC_POLL_PERIOD = 1
pa = PyPerc(
        megacli=MegaCLI(
            runner=MegaCLIRunner(exe="/usr/local/sbin/megacli", adapter=0)
            )
        )

def percpoll(s):
    pa.poll()
    last_event = pa.last_event()
    twisted.internet.reactor.callLater(PERC_POLL_PERIOD, percpoll, "again")

twisted.internet.reactor.callLater(0, percpoll, "first")


def limited_to(limit, iterable):
    total = 0
    for item in iterable:
        if total >= int(limit):
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
                'ad': pa.adapter_details,
                'cf': pa.config_details,
                'ld': pa.ldinfo,
                'pd': pa.pdinfo,
                'pd_to_ld': pa.pd_to_ld,
            })

        elif request.path == '/events/':
            since = args.get('since', None)
            limit = args.get('limit', None)

            if not since:
                events = reversed(pa.events.data)
                events = (item for item in events if item.code not in (30, 113, 236))
                if limit is not None:
                    events = limited_to(limit, events)
                serialized = (item.to_dict() for item in events)
                return ujson.dumps({
                    'success': True,
                    'events': list(serialized),
                    })
            else:
                events = pa.events.find_gt(int(since), limit=limit, filter=lambda event: event.id not in (30, 113, 236))
                serialized = (item.to_dict() for item in events)
                return ujson.dumps({
                    'success': True,
                    'events': list(serialized),
                })

        else:
            print 'bad request: ['+request.path+']'
            return ujson.dumps({'success':False,'message':'unknown request'})


twisted.internet.reactor.listenTCP(50001, twisted.web.server.Site(percapi()))
twisted.internet.reactor.run()

