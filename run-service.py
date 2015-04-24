#!/usr/bin/env python2.7

import sys
import json
from itertools import takewhile

from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.resource import Resource
from twisted.web.util import Redirect
from twisted.internet.protocol import Factory, Protocol
from txsockjs.factory import SockJSResource
from txsockjs.utils import broadcast

from pyperc import PyPerc, MegaCLI, MegaCLIRunner


LISTEN_ADDRESS = '0.0.0.0'  # comma-separated list
LISTEN_PORT = 50001
PERC_POLL_PERIOD = 1.0      # seconds
MEGACLI_EXE = '/opt/MegaRAID/MegaCli/MegaCli64'

log.startLogging(sys.stdout)

connected_users = set()

pyperc = PyPerc(
    megacli=MegaCLI(
        runner=MegaCLIRunner(exe=MEGACLI_EXE, adapter=0)
    )
)


def poll_pyperc():
    last_event = pyperc.last_event()
    pyperc.poll()
    new_event = pyperc.last_event()
    if new_event != last_event:
        broadcast('come get em', connected_users)
    reactor.callLater(PERC_POLL_PERIOD, poll_pyperc)

reactor.callLater(0, poll_pyperc)


def limited_to(limit, iterable):
    total = 0
    for item in iterable:
        if total >= int(limit):
            return
        yield item
        total += 1


class EventBus(Protocol):
    def connectionMade(self):
        connected_users.add(self.transport)
        print 'join', self.transport.getPeer(), ' -- users online:', len(connected_users)

    def dataReceived(self, data):
        print 'rx:', data

    def connectionLost(self, data):
        connected_users.remove(self.transport)
        print 'leave', self.transport.getPeer(), ' -- users online:', len(connected_users)


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
            'ad': pyperc.adapter_details,
            'cf': pyperc.config_details,
            'ld': pyperc.ldinfo,
            'pd': pyperc.pdinfo,
            'pd_to_ld': pyperc.pd_to_ld,
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
            events = reversed(pyperc.events.data)
            events = (item for item in events if item.code not in (30, 113, 236))
            if limit is not None:
                events = limited_to(limit, events)
            events = (item.to_dict() for item in events)
        else:
            events = pyperc.events.find_gt(int(since), limit=limit, filterfunc=lambda event: event.id not in (30, 113, 236))
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
static.putChild("sockjs", File("bower_components/sockjs"))
static.putChild("knockout", File("bower_components/knockout"))
static.putChild("bootstrap", File("bower_components/bootstrap"))
static.putChild("requirejs", File("bower_components/requirejs"))
static.putChild("bootswatch", File("bower_components/bootswatch"))
static.putChild("fontawesome", File("bower_components/fontawesome"))
static.putChild("requirejs-text", File("bower_components/requirejs-text"))

static.putChild("startup.js", File("static/startup.js"))
static.putChild("status_page.js", File("static/status_page.js"))
static.putChild("status_page.html", File("static/status_page.html"))
static.putChild("require.config.js", File("static/require.config.js"))

api = Resource()
api.putChild("events", PercApiEvents())
api.putChild("adapter", PercApiInfo())

root = Resource()
root.putChild("", File("static/index.html"))
root.putChild("api", api)
root.putChild("static", static)
root.putChild("chan", SockJSResource(Factory.forProtocol(EventBus)))

for address in LISTEN_ADDRESS.split(','):
    print 'Will listen on %s:%d' % (address, LISTEN_PORT)
    reactor.listenTCP(LISTEN_PORT, Site(root), interface=address)

reactor.run()

