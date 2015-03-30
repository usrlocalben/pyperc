#!/usr/bin/env python2.7

import re
import sys
import json
import time
import pprint
import subprocess
from datetime import datetime, timedelta

MEGACLI_EXE = '/usr/local/sbin/megacli'
#MEGACLI = '/usr/sbin/megacli'
#MEGACLI = '/home/byates/mega/bin/MegaCli64'

DATAPATH = '/var/lib/pyperc'

DATAFILE   = DATAPATH + '/mega_data.json'
EVENTFILE  = DATAPATH + '/mega_events.json'
EVENTSPOOL = DATAPATH + '/events'

from codetable import codetable
from decoders  import *

MEGADATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
def from_megadate(val):
    return datetime.strptime(val, MEGADATE_FORMAT)
def to_megadate(val):
    return val.strftime(MEGADATE_FORMAT)

def megarun(params):

    assert isinstance(params, (list, tuple))

#    print "exec:", " ".join(params)
    megaout = subprocess.check_output(
        ['sudo', MEGACLI_EXE] + params + ['-a0']
    )
#    open('blob.bin','wb').write(megaout)
    
    first_byte = ord(megaout[0])
    if first_byte != 13:
        raise ValueError("expected 0x0d as the first char of output from megacli")

    # kill opening-CR and trailing-NL, and split
    lines = megaout[1:-1].split("\n")

    exit_str = lines.pop()
    left, right = re.match(r"^([\w ]*)\W*:\W*(\w*)$",exit_str).groups()
    if left != 'Exit Code':
        raise ValueError("expected Exit Code as the last line of output from megacli")
    exit_hex = right[2:]

    return lines#[:-1]


def megasplit(line):
    mid = line.index(':')
    left = line[0:mid].strip()
    right = line[mid+1:].strip()
    return left, right



class perc(object):

    def __init__(self):
        self.pdinfo = [] # hackish... because pollrebuild is called before this is populated
        self.load_events()
        self.first_run = True
        self.refresh()

    def refresh(self):

#        print '=> refresh'

        newevents = self.poll_events()
        self.poll_rebuild()

        realevents = [item for item in newevents if item['code'] not in (30, 113)]
        if realevents or self.first_run:
            self.refresh_adapter()
            self.refresh_pdld_map()
            self.ldinfo = self.get_ld_info(self.ldmap)
            self.refresh_pd_info()
            self.first_run = False

#        print '<= refresh'

    def load_events(self):
        try:
            with open(EVENTFILE, 'r') as fd:
                ee = json.load(fd)
        except IOError:
            ee = {}

        json_events = ee.get('events', [])
        self.events = sorted(json_events, key=lambda item: item['id'], reverse=True)
        try:
            self.last_event = max(self.events, key=lambda item: item['id'])
        except ValueError:
            self.last_event = 0

        # patrol for events without timestamps, and try to create them
        for item in self.events:
            if item['code'] == 44:
                chunks = item['event_data'].split("\n")
                chunk = chunks[0]
                timeset_seconds = int(chunk.split(' ')[-1])
                timeset_datetime = from_megadate(item['time'])
            elif 'sslr' in item:
                adjustment = timedelta(seconds=(timeset_seconds - item['sslr']))
                item['time'] = to_megadate(timeset_datetime - adjustment)

#        print 'last event in ram:', self.last_event
        
    def save_events(self):
        with open(EVENTFILE, 'w') as fd:
            fd.write(json.dumps({'events': self.events}, indent=1))

    def refresh_adapter(self):
        self.adinfo = {}
        self.cfinfo = {}
        adinfo = self.adinfo
        cfinfo = self.cfinfo


        l = megarun(['-AdpAllInfo'])
        l.pop(0) # ''
        l.pop(0) # 'Adapter #0'
        l.pop(0) # ''
        l.pop(0) # '========================...' (78 chars)

        # '         Versions'
        # '     ================' (32 chars)

        """
        it's more consistant to read the lines from the bottom-to-top.
        start a block.
        collect lines, heading up.
        get to a =========== break?
        we're done.
        next line up has the title for the block we just did.
        start a new block
        continue.
        """
        sections = {}
        bucket = []
        state = 'bucket'
        for line in reversed(l):
            if state == 'bucket':
                if line == '                ================':
                    state = 'edge'
                else:
                    bucket.append(line)
            elif state == 'edge':
                title = line.strip()
                sections[title] = bucket[::-1]
                bucket = []
                state = 'bucket'
        #endfor lines



        m = {
             'Product Name'     : 'product'
            ,'Serial No'        : 'serial_number'
            ,'FW Package Build' : 'firmware'
        }
        for l,r in ( megasplit(s) for s in sections['Versions'] if s != '' ):
            if l not in m: raise NameError("unhandled adapter attribute pci info '%s'='%s'" % (l,r))
            adinfo[ m[l] ] = r


        block = "\n".join(sections['PCI Info'])
        chunks = block.split("\n\n")
        if len(chunks) != 4:
            raise ValueError("i expected 4 chunks in the PCI info block, but instead there were %d" % (len(chunks)))

        m = {
             'Vendor Id'     : 'pci_vendor'
            ,'Device Id'     : 'pci_device'
            ,'SubVendorId'   : 'pci_subvendor'
            ,'SubDeviceId'   : 'pci_subdevice'
            ,'Controller Id' : 'controller_id' # '0000'
        }
        for l,r in ( megasplit(s) for s in chunks[0].split("\n") if s != '' ):
            if l not in m: raise NameError("unhandled adapter attribute pci info '%s'='%s'" % (l,r))
            adinfo[ m[l] ] = r


        # chunk[3] has the list of raw sas ports and their sas addresses
        portlines = chunks[3].strip().split("\n")
        portlines.pop(0) # 'Number of Backend Port: 8'
        portlines.pop(0) # 'Port  :  Address'
        self.adinfo['portlist'] = {}
        for s in portlines:
            parts = re.split(r"\s+",s,2) # split on whitespace, "0        1221000000000000"
            l = parts[0]
            r = parts[1]
            self.adinfo['portlist'][l] = r

        self.adinfo['portcount'] = len(self.adinfo['portlist'])


        m = {
              'SAS Address'                       : ( 'sas_address'           ,decode_noop )
             ,'BBU'                               : ( 'has_bbu'               ,decode_present )
             ,'Alarm'                             : ( 'has_alarm'             ,decode_present )
             ,'NVRAM'                             : ( 'has_nvram'             ,decode_present )
             ,'Serial Debugger'                   : ( 'has_debugger'          ,decode_present )
             ,'Memory'                            : ( 'has_memory'            ,decode_present )
             ,'Flash'                             : ( 'has_flash'             ,decode_present )
             ,'Memory Size'                       : ( 'memory_size'           ,hmem_to_int )
             ,'TPM'                               : ( 'has_tpm'               ,decode_present )
             ,'On board Expander'                 : ( 'has_expander'          ,decode_present )
             ,'Upgrade Key'                       : ( 'upgrade_key'           ,decode_noop )
             ,'Temperature sensor for ROC'        : ( 'has_sensor_roc'        ,decode_present )
             ,'Temperature sensor for controller' : ( 'has_sensor_controller' ,decode_present )
        }
        for l,r in ( megasplit(s) for s in sections['HW Configuration'] if s != '' ):
            if l not in m: raise NameError("unhandled adapter attribute hw config '%s'='%s'" % (l,r))
            setting = m[l]
            if setting is None: continue
            key,xform = setting
            adinfo[key] = xform(r)



        m = {
             'Current Time'                    : ( 'time', decode_strtotime )
            ,'Predictive Fail Poll Interval'   : ( 'pf_poll_seconds', decode_intsec ) # '300sec' -> 300
            ,'Interrupt Throttle Active Count' : None
            ,'Interrupt Throttle Completion'   : None
            ,'Rebuild Rate'                    : ( 'rate_rebuild', decode_intpct )
            ,'PR Rate'                         : ( 'rate_pr', decode_intpct )
            ,'BGI Rate'                        : ( 'rate_bgi', decode_intpct )
            ,'Check Consistency Rate'          : ( 'rate_cc', decode_intpct )
            ,'Reconstruction Rate'             : ( 'rate_recon', decode_intpct )
            ,'Cache Flush Interval'            : ( 'cache_flush_seconds', decode_intsec ) # '4s' assumes NNNNs
            ,'Max Drives to Spinup at One Time': None
            ,'Delay Among Spinup Groups'       : None
            ,'Physical Drive Coercion Mode'    : ( 'rounding_size', hmem_to_int ) # '128MB' -> 128
            ,'Cluster Mode'                    : None
            ,'Alarm'                           : ( 'alarm_state', decode_noop ) # 'Disabled' -- does enabled mean the alarm is emitting sound?
            ,'Auto Rebuild'                    : ( 'auto_rebuild', decode_noop ) # 'Enabled'
            ,'Battery Warning'                 : ( 'battery_warning', decode_noop ) # 'Enabled'
            ,'Ecc Bucket Size'                 : ( 'ecc_bucket_size', decode_int ) # ???
            ,'Ecc Bucket Leak Rate'            : ( 'ecc_bucket_leak_minutes', decode_minutes ) # '1440 minutes'
            ,'Restore HotSpare on Insertion'   : None
            ,'Expose Enclosure Devices'        : None
            ,'Maintain PD Fail History'        : None
            ,'Host Request Reordering'         : None # is this related to TCQ?
            ,'Auto Detect BackPlane Enabled'   : None
            ,'Load Balance Mode'               : None
            ,'Use FDE Only'                    : None
            ,'Security Key Assigned'           : None
            ,'Security Key Failed'             : None
            ,'Security Key Not Backedup'       : None
            ,'Any Offline VD Cache Preserved'  : None
            ,'Allow Boot with Preserved Cache' : None
            ,'Disable Online Controller Reset' : None
            ,'PFK in NVRAM'                    : None # what is PFK???
            ,'Use disk activity for locate'    : None
            ,'Default LD PowerSave Policy'     : None # 'Controller Defined'
            ,'Maximum number of direct attached drives to spin up in 1 min' : None # '0'
            ,'Auto Enhanced Import'            : None # 'No'
            ,'POST delay'                      : None # '90 seconds'
        }
        for l,r in ( megasplit(s) for s in sections['Settings'] if s != '' ):
            if l not in m: raise NameError("unhandled adapter settings attribute '%s'='%s'" % (l,r))
            setting = m[l]
            if setting is None: continue
            key,xform = setting
            cfinfo[key] = xform(r)


        #----------------------------------------------------------------
        # i will ignore everything here except for the raid level list
        # this also assumes that the first line of this block is the RAID Levels Supported: line
        l,r = megasplit(sections['Capabilities'][0])
        adinfo['raidlevels'] = r.split(", ")


        #----------------------------------------------------------------
        # assume first line is 'ecc bucket count'
        l,r = megasplit(sections['Status'][0])
        adinfo['ecc_bucket_count'] = int(r)


        #----------------------------------------------------------------
        # this section could be converted into an array of bools, and justkeep the original text...
        # i will ignore it for now, as well as VD and PD operations


        #----------------------------------------------------------------
        for l,r in ( megasplit(s) for s in sections['Error Counters'] if s != '' ):
            if   l == 'Memory Correctable Errors':   cfinfo['memory_errors_correctable'] = decode_int(r)
            elif l == 'Memory Uncorrectable Errors': cfinfo['memory_errors_uncorrectable'] = decode_int(r)
            else:
                raise NameError("unhandled adapter attribute '%s'='%s'"%(l,r))

    #enddef refresh


    def get_ld_info(self, ldmap):

        #-- fetch LD details --------------------------------------------------
        # LDInfo needs to be passed a target_id, not an index.
        # ldmap made earlier is used to get this sequence
        ldinfo = []
        for ldid in ldmap:

            lines = megarun(['-LDInfo','-L'+str(ldid)])
            lines.pop(0) #''
            lines.pop(0) #''
            lines.pop(0) #'Adapter 0 -- Virtual Drive Information:'
            lines.pop(0) #'Virtual Drive: 0 (Target Id: 0)'

            a = {}
            for l,r in ( megasplit(l) for l in lines if l != '' ):
                a['id'] = ldid
                if   l == 'Name':                      a['name']                 = '(unnamed)' if r=='' else r
                elif l == 'RAID Level':                a['raid_level']           = decode_raidlevel(r)
                elif l == 'Size':                      a['size']                 = r
                elif l == 'State':                     a['state']                = decode_ld_state(r)
                elif l == 'Strip Size':                a['stripe']               = decode_stripe_size(r)
                elif l == 'Number Of Drives':          a['raid_devices']         = decode_int(r)
                elif l == 'Span Depth':                a['span_depth']           = decode_int(r)
                elif l == 'Number Of Drives per span': a['span_drives']          = decode_int(r)
                elif l == 'Default Cache Policy':      a['cache_policy_default'] = decode_cache_policy(r)
                elif l == 'Current Cache Policy':      a['cache_policy']         = decode_cache_policy(r)
                elif l == 'Access Policy':             a['access']               = decode_noop(r)
                elif l == 'Disk Cache Policy':         a['cache_policy_disk']    = r
                elif l == 'Encryption Type':           a['encryption']           = r
                elif l == 'Ongoing Progresses':        pass
                elif l == 'Background Initialization':
                    junk = r.split(' ')
                    a['init_pct']     = junk[1][:-2]
                    a['init_elapsed'] = junk[3]
                elif l == 'Mirror Data':               pass # '3.637 TB'
                elif l == 'Default Access Policy':     pass # 'Read/Write'
                elif l == 'Current Access Policy':     pass # 'Read/Write'
                elif l == 'Is VD Cached':              pass # 'No'
                else:
                    raise ValueError("unknown LD attribute '%s'='%s'"%(l,r))
            #endfor lines
            ldinfo.append(a)
        #endfor ldmap
        return ldinfo



    def refresh_pd_info(self):

        pdinfo = []
        pdidx = {}
        for pd in self.get_raw_pd_list():

            #'WD-WMC1T0421813WDC WD20EFRX-68AX9N0                    80.00A80'
            # also see details in get_raw_pdlist
            ser = pd['Inquiry Data'][0:20].strip()
            mod = pd['Inquiry Data'][20:60].strip()
            ver = pd['Inquiry Data'][60:].strip()
            #ser,mod,ver = re.split("\s+",pd['Inquiry Data'])

            a = {
                 'enclosure'       : '' if pd['Enclosure Device ID'] == 'N/A' else pd['Enclosure Device ID']
                ,'slot'            : int(pd['Slot Number'])
                ,'device'          : int(pd['Device Id'])
                ,'sequence'        : int(pd['Sequence Number'])
                ,'errors_media'    : int(pd['Media Error Count'])
                ,'errors_other'    : int(pd['Other Error Count'])
#                ,'predicitive_failure_count'] = int(pd['Predictive Failure Count'])
                ,'type'            : pd['PD Type']
                ,'size_raw'        : decode_size(pd['Raw Size'])
                ,'size_noncoerced' : decode_size(pd['Non Coerced Size'])
                ,'size_coerced'    : decode_size(pd['Coerced Size'])
                ,'state'           : decode_pd_state(pd['Firmware state'])
                ,'connected_port_number' : pd['Connected Port Number']
                ,'inq_serial'      : ser
                ,'inq_model'       : mod
                ,'inq_version'     : ver
                ,'locked'          : pd['Locked']
                ,'foreign_state'   : pd['Foreign State']
                ,'device_speed'    : pd['Device Speed']
                ,'link_speed'      : pd['Link Speed']
                ,'media_type'      : pd['Media Type']
                ,'enclosure_position' : pd['Enclosure position']
                ,'firmware_level'  : pd['Device Firmware Level']
                ,'shield_counter'  : pd['Shield Counter']
                ,'write_cache'     : pd['Drive\'s write cache']=='Enabled'
            }
            if 'Foreign Secure' in pd: a['foreign_secure'] = pd['Foreign Secure']

            if a['state'] == 'rebuild':
                pct,elapsed = self.get_rebuild_progress(a['slot'])
                a['rebuild_pct'] = pct
                a['rebuild_elapsed'] = elapsed

            pdinfo.append(a)
            pdidx[ (a['slot'],a['device'],) ] = a

        #endfor raw pdlist

        self.pdinfo = pdinfo
        self.pdidx = pdidx


    def poll_rebuild(self):
        for i,pd in enumerate(self.pdinfo):
            if pd['state'] != 'rebuild': continue
            pct,elapsed = self.get_rebuild_progress(pd['slot'])
            self.pdinfo[i]['rebuild_pct'] = pct
            self.pdinfo[i]['rebuild_elapsed'] = elapsed
        

    def get_event_markers(self):
        lines = megarun(['-AdpEventLog','-GetEventLogInfo'])
        lines.pop(0) # ''
        lines.pop(0) # 'Adapter #0'
        lines.pop(0) # ''

        lines.pop() # ''
        str = lines.pop() # 'Success in AdpEventLog'
        if str != 'Success in AdpEventLog':
            raise ValueError('expected Success in AdpEventLog')
        lines.pop() # ''

        # 'blahblah Seqnum: 0xabcdabcd'  =>  { 'blahblah' : int(abcdabcd,16) }
        splits = ( megasplit(l) for l in lines )
        return { l[:-07].lower() : int(r[2:],16) for l,r in splits }

        """
        evidx = {}
        for l in lines:
            # 'blahblah Seqnum: 0xabcdabcd'  =>  { 'blahblah' : int(abcdabcd,16) }
            l,r = megasplit(l)
            hexdigits = r[2:]
            evidx[ l[:-7].lower() ] = int(hexdigits,16)

        return evidx
        """
       


    def get_raw_pd_list(self):

        lines = megarun(['-PDList'])
        raw = "\n".join(lines)
        blocks = "\n".join(lines).split("\n\n")
        xx = blocks.pop(0).strip()
        yy = blocks.pop()
        if xx != 'Adapter #0': raise Error("expected first pdlist block to have Adapter #0")
        if yy != '': raise Error("expected empty last block in pdlist output")

        pdlist = []
        for block in blocks:
            if block == '': continue

            a = {}
            for line in block.split("\n"):
                try:
                    l,r = re.match(r"^([\w\'\(\)\-\. ]+):\W*(.*)$",line).groups()
                except:
                    print "failed to match/split [%s]" % ( line )
                    raise
                #XXX special case for the drive data because we need to preserve exact chars
                """
Inquiry Data:             Z1M1971LST500NM0011                             SN03
Inquiry Data:      WD-WMC1T0421813WDC WD20EFRX-68AX9N0                    80.00A80
Inquiry Data: BTWL3134009C300PGN  INTEL SSDSC2BB300G4                     D2010350
0123456789012345
          111111
              01234567890123456789012345678901234567890123456789012345678901234567890
                        1111111111222222222233333333334444444444555555555566666666667
                """
                if l.strip() == 'Inquiry Data':
                    a[l.strip()] = line[14:]
                else:
                    a[l.strip()] = r.strip()
            pdlist.append(a)

        return pdlist



    def get_rebuild_progress(self, slot):
        lines = megarun(['-PDRbld','-ShowProg','-PhysDrv',"[:"+str(slot)+"]"])
        # complete: ['                                     ', 'Device(Encl-N/A Slot-2) is not in rebuild process', '']
        res = lines[1]
        if res.endswith('is not in rebuild process'):
            return 100,0

        # forgot to add an example of the in-progress output :(
        blah = res.split(' ')
        pct = blah[10][:-1]
        minutes = int(blah[12])
        return pct, min



    def poll_events(self):

        evidx = self.get_event_markers()
        if self.last_event == evidx['newest']:
            return []

        # have megacli write the log, then read it
        fname = EVENTSPOOL + '/' + datetime.utcnow().strftime('event_%Y%m%d_%H%M%S.txt')
        lines = megarun(['-AdpEventLog','-GetEvents','-f',fname])
        newevents = self.merge_events(self.read_event_file(fname))

        # clear the log, and check the markers to see if
        # anything arrived between lastread & clear
        if len(newevents) > 1:
            lines = megarun(['-AdpEventLog','-Clear'])
            newmarkers = self.get_event_markers()
            if newmarkers['clear'] != self.last_event+1:
                print "log entries arrived while clearing! my last:%d, clear:%d" % (self.last_event, newmarkers['clear'])
                fname = EVENTSPOOL + '/' + datetime.utcnow().strftime('event_%Y%m%d_%H%M%S.all')
                lines = megarun(['-AdpEventLog','-IncludeDeleted','-f',fname])
                newevents += self.merge_events(self.read_event_file(fname))

        self.save_events()
        print "pollEvents: merged %d new events" % (len(newevents))
        return newevents

    def merge_events(self, evlst):
        existing_ids = [item['id'] for item in self.events]
        new_events = [item for item in evlst if item['id'] not in existing_ids]
        self.events = sorted(self.events + new_events, key=lambda k: k['id'], reverse=True)
        self.last_event = self.events[0]['id']
        return new_events

    def clear_events(self):
        self.events = []
        self.last_event = 0

    def read_event_file(self, fname):

        with open(fname, 'r') as fd:
            events = fd.read()

        chunks = events.split("seqNum: 0x")
        chunks.pop(0) # skip the header

        newevents = []
        lastevent = 0
        for chunk in chunks:

            a = {}
            p1,event_data = chunk.strip().split("\nEvent Data:\n===========\n")

            p1lines = p1.split("\n")
            a['id'] = int(p1lines.pop(0),16)
            lastevent = max(lastevent, a['id'])

            for line in p1lines:
                if line == '': continue
                try:
                    l,r = re.match(r"^([\w ]+):\W*(.*)$",line).groups()
                except:
                    raise ValueError("failed to split [%s]" % (line))

                if   l == 'Time':   a['time']   = decode_event_time(r).isoformat()
                elif l == 'Code':   a['code']   = int(r[2:],16)
                elif l == 'Class':  a['level']  = int(r)
                elif l == 'Locale': a['locale'] = int(r[2:],16) # '0x20'
                elif l == 'Event Description' : a['description'] = r
                elif l == 'Seconds since last reboot' : a['sslr'] = int(r)
                else:
                    raise Error("unhandled event attribute '%s'='%s'"%(l,r))


            if a['code'] not in codetable:
                raise ValueError("unhandled code level(%s), code(%s), descr(%s)"%(a['level'],a['code'],a['description']))

            a['event_data'] = event_data
            newevents.append(a)

        #endfor event file chunks
        return newevents

    def refresh_pdld_map(self):

        lines = megarun(['-LdPdInfo'])

        lines.pop(0) # ''
        lines.pop(0) # 'Adapter #0'
        lines.pop(0) # ''
        l,r = megasplit(lines.pop(0)) # 'Number of Virtual Disks: 2'
        if l != 'Number of Virtual Disks':
            raise ValueError("expected 'Number of Virtual Disks'");
        virtual_disks = int(r)

        # rejoin and resplit
        chunks = "\n".join(lines).split("Virtual Drive: ")
        chunks.pop(0) # remove empty element -- present since the data begins with the explode-pattern

        pdtab = {}
        ldmap = {}
        for vdblock in chunks:
            lines = vdblock.split("\n")
            l = lines.pop(0)
            fields = l.split(' ')
            vdnum = int(fields[0])
            target_id = int(fields[3][0:-1])

            # vdnum is 0,1,2,...,n, where target_id could be 1,3,4,7.
            ldmap[ vdnum ] = target_id

            # skip past the LU details, which i could gather here, but I already wrote a parser elsewhere
            while True:
                x = lines.pop(0)
                if x.startswith('Number of Spans'): break

            current_span = None
            current_pd = None
            current_pd_enclosure_device_id = None
            current_pd_slot_number = None
            current_pd_device_id = None

            pd_to_ld = {}

            def emit(volume, span, unit, device):
                #print 'span:', span, ', spandev:', unit, ', device:', device
                pd_to_ld[device] = {'ld': volume, 'span': span, 'unit': unit}


            pdtab[target_id] = {}
            for x in lines:
                if   x.startswith('Span: '):
                    span_id = x.split(' ')[1]
                    if current_span:
                        emit(vdnum, current_span, current_pd, current_pd_device_id)
                        current_pd = None
                    current_span = span_id
                    #pdtab[target_id][span_id] = {}
                elif x.startswith('PD: '):
                    pd_id = x.split(' ')[1]
                    if current_pd:
                        emit(vdnum, current_span, current_pd, current_pd_device_id)
                    current_pd = pd_id
                    #pdtab[target_id][span_id][pd_id] = {}
                elif x.startswith('Enclosure Device ID: '):
                    enc = x[21:].strip()
                    if enc == 'N/A': enc = ''
                    current_pd_enclosure_device_id = enc
                    #pdtab[target_id][span_id][pd_id]['enclosure'] = enc
                elif x.startswith('Slot Number: '):
                    current_pd_slot_number = x[13:]
                    #pdtab[target_id][span_id][pd_id]['slot']      = x[13:]
                elif x.startswith('Device Id: '):
                    current_pd_device_id = x[11:]
                    #pdtab[target_id][span_id][pd_id]['device']    = x[11:]
            #endfor lines
            if current_pd:
                emit(vdnum, current_span, current_pd, current_pd_device_id)

        #endfor chunks

        #self.pdtab = {} #pdtab
        self.ldmap = ldmap
        self.pd_to_ld = pd_to_ld
        #print pd_to_ld

    #enddef getPDLDMap



def main():

    p = perc()
    print 'done building'

    p.clearEvents()

    ev = p.readEventFile('/var/lib/pyperc/events/events_20140607_144224')
    n = p.mergeEvents(ev)
    print 'loaded %d new events from disk.' % ( n )
    ev = p.readEventFile('/var/lib/pyperc/events/events_20140607_144700')
    n = p.mergeEvents(ev)
    print 'loaded %d new events from disk.' % ( n )
    p.saveEvents()
    print 'event table saved.'

    sys.exit(0)



    cnt = 0

    evs = sorted(p.events, key=lambda k: -k['id'])

    for e in evs:
#        if e['class'] == 0: continue
        if e['code'] in [ 236, 113 ]: continue
        pprint.pprint(e)
        cnt += 1
        if cnt == 10: break

"""
setting the time
-AdpGetTime
-AdpSetTime yyyymmdd hh:mm:ss

from shell:
    megacli -AdpSetTime `date -u "+%Y%m%d %T"` -a0
"""


if __name__ == '__main__':
    sys.exit(main())

