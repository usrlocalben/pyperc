#!/usr/bin/env python2.7

import os
import re
import sys
import json
import time
import pprint
import subprocess
from datetime import datetime, timedelta

from events import MegaEvent
from sortedcollection import SortedCollection, NotUniqueError

MEGACLI_EXE = '/usr/local/sbin/megacli'
TIMESET_EVENT_CODE = 44

class PyPerc(object):

    def __init__(self, megacli):
        self.megacli = megacli
        self.load() # load first, because it can cause events to occur
        self.events = SortedCollection() #limit=1000)
        self.load_event_history()
        self.loaded = True

    def load(self):
        self.adapter_details, self.config_details = self.megacli.get_AdpAllInfo()
        self.ld_to_target, self.pd_to_ld = self.megacli.get_ldpd_info()

        self.ldinfo = []
        for ld in self.ld_to_target:
            self.ldinfo.append(self.megacli.get_LDInfo(ld))

        self.pdinfo, _ = self.megacli.get_PDList()
        self.loaded = True

    def poll(self):
        assert self.loaded

        total_new_events = self.poll_events()
        self.poll_rebuild()

        new_events = self.events.find(limit=total_new_events, reverse=True)
        xcnt = 0
        for event in new_events:
            print 'new:', event.id, event.code, event.description
            xcnt += 1
            if xcnt > 15:
                print '...and more...'
                break

        new_events = self.events.find(limit=total_new_events, reverse=True)
        new_important_events = any(event for event in new_events if event.code not in (30, 113))
        if new_important_events:
            print 'there were new important events!'
            self.load()

    def poll_rebuild(self):
        for pd in self.pdinfo:
            if pd['state'] == 'rebuild':
                pct, elapsed = self.megacli.get_rebuild_progress(pd['slot'])
                pd['rebuild_pct'] = pct
                pd['rebuild_elapsed'] = elapsed

    def last_event(self):
        return self.events.data[-1]

    def load_event_history(self):
        tmpnm = '/tmp/megacli_all_events.txt'
        #try:
        self.megacli.dump_events_deleted(tmpnm)
        #except CalledProcessError:
        #    pass
        total_events, _ = self.merge_event_file(tmpnm)
       
        print 'read', total_events, 'events from controller'
        self.try_to_fixup_sslrs()

    def try_to_fixup_sslrs(self):
        # patrol for events without timestamps, and try to create them
        total_fixups = 0
        total_resets = 0
        total_failed = 0

        timeset_seconds = None
        timeset_datetime = None
        for event in reversed(self.events.data):
            if event.code == TIMESET_EVENT_CODE:
                line = event.data.split("\n")[0]
                timeset_seconds = int(line.split(' ')[-1])
                timeset_datetime = event.time
                total_resets += 1
            elif event.sslr:
                if timeset_seconds:
                    adjustment = timedelta(seconds=(timeset_seconds - event.sslr))
                    event.time = timeset_datetime - adjustment
                    total_fixups += 1
                else:
                    total_failed += 1

            if event.code == 0:
                # invalidate the time data as we pass a Power On event (code==0)
                timeset_seconds = None
                timeset_datetime = None

        print 'fixed %d timestamps and saw %d clock-sets. %d could not be fixed.' %\
              (total_fixups, total_resets, total_failed)

    def merge_event_file(self, fname):
        total_events = 0
        dupes = []
        with open(fname, 'r') as fd:
            for event in MegaEvent.stream(fd):
                try:
                    self.events.insert(event.id, event)
                except NotUniqueError:
                    dupes.append(event.id)
                else:
                    total_events += 1
        return total_events, dupes
        
    def poll_events(self):
        last_event = self.last_event()
        if last_event:
            last_id = last_event.id
        else:
            last_id = 0

        newest, _ = self.megacli.get_event_markers()
        #print 'polling: my latest id is', last_id, 'and the controllers is', newest
        if last_id == newest:
            return 0

        # have megacli write the log, then read it
        total_new = newest - last_id
        
        total_events = 0
        tmpnm = '/tmp/megacli_more_events.txt'
        self.megacli.dump_recent_events(tmpnm, total_new * 2)
        added_events, dupes = self.merge_event_file(tmpnm)
        total_events += added_events

        if not dupes:
            raise Exception("event poll request may have missed data")

        print 'poll_events merged', total_events, 'new events'
        return total_events

