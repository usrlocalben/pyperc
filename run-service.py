#!/usr/bin/env python2.7

import time
import json
import urlparse
from itertools import takewhile

import twisted.web.server

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.static import File

from pyperc import PyPerc, MegaCLI, MegaCLIRunner


PERC_POLL_PERIOD = 1
pa = PyPerc(
        megacli=MegaCLI(
            runner=MegaCLIRunner(exe="/opt/MegaRAID/MegaCli/MegaCli64", adapter=0)
            )
        )

def percpoll(s):
    pa.poll()
    last_event = pa.last_event()
    reactor.callLater(PERC_POLL_PERIOD, percpoll, "again")

reactor.callLater(0, percpoll, "first")


def limited_to(limit, iterable):
    total = 0
    for item in iterable:
        if total >= int(limit):
            return
        yield item
        total += 1


class PercApiInfo(Resource):
    isLeaf = True
    request_count = 0

    def render_GET(self, request):

        #remote_host = request.getHost() #( twisted.internet.address.IPv4Address .host, .port, .type )
        #print "adapter %s %s" % (remote_host.host, request.uri)

        self.request_count += 1
        request.setHeader("Content-type", "application/json")

        return json.dumps({
            'success': True,
            'ad': pa.adapter_details,
            'cf': pa.config_details,
            'ld': pa.ldinfo,
            'pd': pa.pdinfo,
            'pd_to_ld': pa.pd_to_ld,
        })


class PercApiEvents(Resource):
    isLeaf = True
    request_count = 0

    def render_GET(self, request):
        #remote_host = request.getHost() #( twisted.internet.address.IPv4Address .host, .port, .type )
        #print "events - %s %s" % (remote_host.host, request.uri)

        self.request_count += 1
        request.setHeader("Content-type", "application/json")

        since = request.args.get('since', [None])[0]
        limit = request.args.get('limit', [None])[0]

        ignore = (30, 113, 236)

        if not since:
            events = reversed(pa.events.data)
            events = (item for item in events if item.code not in (30, 113, 236))
            if limit is not None:
                events = limited_to(limit, events)
            events = (item.to_dict() for item in events)
        else:
            events = pa.events.find_gt(int(since), limit=limit, filter=lambda event: event.id not in (30, 113, 236))
            events = (item.to_dict() for item in events)

        events = (item for item in events if item['code'] not in ignore)
        events = sorted(events, key=lambda item: item['id'])
        return json.dumps({
            'success': True,
            'events': events,
            })

static = Resource()
static.putChild("jquery", File("bower_components/jquery"))
static.putChild("moment", File("bower_components/moment"))
static.putChild("knockout", File("bower_components/knockout"))
static.putChild("bootstrap", File("bower_components/bootstrap"))
static.putChild("bootswatch", File("bower_components/bootswatch"))
static.putChild("fontawesome", File("bower_components/fontawesome"))
static.putChild("dashboard.js", File("static/dashboard.js"))
static.putChild("require.js", File("static/require.js"))

api = Resource()
api.putChild("events", PercApiEvents())
api.putChild("adapter", PercApiInfo())

root = Resource()
root.putChild("api", api)
root.putChild("static", static)
root.putChild("home", File("static/dashboard.html"))

reactor.listenTCP(50001, twisted.web.server.Site(root))
reactor.run()

