#!/usr/bin/env python2.7

import re
import sys

from decoders import *
from event_codes import MEGA_EVENT_CODES
from utils import megasplit, from_megadate

class MegaEvent(object):
    def __init__(self, id, code, level, locale, description, data, time=None, sslr=None):
        if time is None and sslr: pass
        elif sslr is None and time: pass
        else: raise Exception("events must have either a time or seconds-since-last-reboot")

        if int(code) not in MEGA_EVENT_CODES:
            raise ValueError("unhandled code level(%s), code(%s), descr(%s)" %\
                                (a['level'], a['code'], a['description']))

        self.id = int(id)
        self.code = int(code)
        self.data = data
        self.level = int(level)
        self.locale = locale
        self.description = description

        self.time = time
        self.sslr = int(sslr) if sslr is not None else None

    def to_dict(self):
        data = {
            'id': self.id,
            'code': self.code,
            'data': self.data,
            'level': self.level,
            'locale': self.locale,
            'description': self.description,
        }
        if self.time:
            data['time'] = self.time.isoformat() #to_megadate(self.time) #.isoformat()
        elif self.sslr:
            data['sslr'] = self.sslr
        return data

    @classmethod
    def from_dict(cls, data):
        time_ = from_megadate(data['time']) if 'time' in data else None
        return cls(
            id=data['id'],
            code=data['code'],
            data=data['data'],
            level=data['level'],
            locale=data['locale'],
            description=data['description'],
            time=time_,
            sslr=data.get('sslr'),
        )

    @classmethod
    def stream(cls, fd):

        #
        # advance until the title appears
        # "Adapter: 0 - Number of Events : 9987"
        # 
        """
        adapter_id = None
        total_events = None
        for line in fd:
            match = re.match(r"Adapter: ([0-9]+) - Number of Events : ([0-9]+)", line);
            if match:
                adapter_id, total_events = match.groups()
                adapter_id = int(adapter_id)
                total_events = int(total_events)
                break

        if adapter_id is None:
            raise Exception("end of stream while reading event data, searching for title")
        """

        sd = {
            'seqnum': None,
            'sslr': None,
            'time': None,
            'code': None,
            'level': None,
            'locale': None,
            'description': None,
            'linestack': [],
        }
        def emit():
            assert sd['linestack'][0] == '==========='
            sd['linestack'].pop(0)
            event_data = '\n'.join(sd['linestack']).strip()
            return cls(
                id=sd['seqnum'],
                code=sd['code'],
                level=sd['level'],
                locale=sd['locale'],
                description=sd['description'],
                data=event_data,
                sslr=sd['sslr'],
                time=sd['time'],
            )
        def reset():
            sd['sslr'] = None
            sd['time'] = None
            sd['linestack'] = []

        emit_count = 0
        for line in fd:

            if line.startswith('seqNum:'):
                match = re.match(r"seqNum:\W*0x([0-9a-f]+)", line)
                if sd['seqnum']:
                    yield emit()
                    emit_count += 1
                    reset()
                hex, = match.groups()
                sd['seqnum'] = int(hex, 16)
            elif line.startswith('Time:'):
                _, timestr = megasplit(line)
                sd['time'] = decode_event_time(timestr)
            elif line.startswith('Seconds since last reboot:'):
                match = re.match(r"Seconds since last reboot:\W*([0-9]+)", line)
                sd['sslr'], = match.groups()
            elif line.startswith('Code:'):
                match = re.match(r"Code:\W*0x([0-9a-f]+)", line)
                hex, = match.groups()
                sd['code'] = int(hex, 16)
            elif line.startswith('Locale:'):
                match = re.match(r"Locale:\W*0x([0-9a-f]+)", line)
                hex, = match.groups()
                sd['locale'] = int(hex, 16)
            elif line.startswith('Class:'):
                match = re.match(r"Class:\W*([0-9]+)", line)
                levelstr, = match.groups()
                sd['level'] = int(levelstr)
            elif line.startswith('Event Description:'):
                _, sd['description'] = megasplit(line)
            elif line.startswith('Event Data:'):
                sd['linestack'] = []
            else:
                sd['linestack'].append(line.strip())

        #endfor streamlines
        if sd['seqnum']:
            yield emit()
            emit_count += 1

        """
        if emit_count != total_events:
            raise Exception("input stream indicated %d events, but %d events were detected" % (total_events, emit_count))
        """

