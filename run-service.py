#!/usr/bin/env python2.7

import sys
import json

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
        bus_broadcast('events', {})
    reactor.callLater(PERC_POLL_PERIOD, poll_pyperc)

reactor.callLater(0, poll_pyperc)


def limited_to(limit, iterable):
    total = 0
    for item in iterable:
        if total >= int(limit):
            return
        yield item
        total += 1


def bus_message(channel, data):
    return json.dumps({
        'ch': channel,
        'data': data
    })

def bus_broadcast(channel, data):
    broadcast(bus_message(channel, data), connected_users)

class EventBus(Protocol):
    def connectionMade(self):
        connected_users.add(self.transport)
        print 'join', self.transport.getPeer(), ' -- users online:', len(connected_users)
        self.transport.write(bus_message('hello', 'welcome'))

    def dataReceived(self, data):
        print 'rx:', data

    def connectionLost(self, data):
        connected_users.remove(self.transport)
        print 'leave', self.transport.getPeer(), ' -- users online:', len(connected_users)


class PercApiInfo(Resource):
    isLeaf = True

    def render_GET(self, request):
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

    def render_GET(self, request):

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

        request.setHeader("Content-type", "application/json")
        return json.dumps({
            'success': True,
            'events': events,
            })


api = Resource()
api.putChild("events", PercApiEvents())
api.putChild("adapter", PercApiInfo())

root = Resource()
root.putChild("", Redirect("static/"))
root.putChild("api", api)
root.putChild("static", File("dist"))   # compiled
#root.putChild("static", File("static"))    # source
root.putChild("chan", SockJSResource(Factory.forProtocol(EventBus)))

for address in LISTEN_ADDRESS.split(','):
    print 'Will listen on %s:%d' % (address, LISTEN_PORT)
    reactor.listenTCP(LISTEN_PORT, Site(root), interface=address)

reactor.run()

