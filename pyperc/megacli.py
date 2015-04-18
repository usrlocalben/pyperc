"""
MegaCLI, wrapper for the LSI/Dell megacli binary
"MegaCLI SAS RAID Management Tool  Ver 8.02.21 Oct 21, 2011"
"""

import re
import subprocess
from utils import megasplit
from decoders import *


class MegaCLIRunner(object):
    def __init__(self, exe, adapter):
        self.command = ['sudo', exe]
        self.adapter = ['-a%d' % adapter]

    def run(self, params):
        assert isinstance(params, list)

        #print "exec:", " ".join(params)
        output = subprocess.check_output(
            self.command + params + self.adapter
        )
        return output
        #open('blob.bin','wb').write(megaout)


class MegaCLI(object):

    def __init__(self, runner):
        self.runner = runner

    def megarun(self, params):
        megaout = self.runner.run(params)

        first_byte = ord(megaout[0])
        if first_byte != 13:
            raise Exception("expected 0x0d as the first char of output from megacli")

        # kill opening-CR and trailing-NL, and split
        lines = megaout[1:-1].split("\n")

        exit_str = lines.pop()
        left, right = re.match(r"^([\w ]*)\W*:\W*(\w*)$", exit_str).groups()
        if left != 'Exit Code':
            raise ValueError("expected Exit Code as the last line of output from megacli")
        #exit_hex = right[2:]
        return lines

    def get_ldpd_info(self):

        lines = self.megarun(['-LdPdInfo'])

        lines.pop(0) # ''
        lines.pop(0) # 'Adapter #0'
        lines.pop(0) # ''
        l,r = megasplit(lines.pop(0)) # 'Number of Virtual Disks: 2'
        if l != 'Number of Virtual Disks':
            raise ValueError("expected 'Number of Virtual Disks'")
        total_volumes = int(r)

        # rejoin and resplit
        chunks = "\n".join(lines).split("Virtual Drive: ")
        chunks.pop(0) # remove empty element -- present since the data begins with the explode-pattern

        ldmap = {}
        pd_to_ld = {}
        for vdblock in chunks:

            lines = vdblock.split("\n")
            l = lines.pop(0)
            fields = l.split(' ')
            volume_id = int(fields[0])
            target_id = int(fields[3][0:-1])

            #
            # vdnum is 0,1,2,...,n, where target_id could be 1,3,4,7.
            #
            ldmap[volume_id] = target_id

            #
            # skip past the LU details
            #
            while True:
                x = lines.pop(0)
                if x.startswith('Number of Spans'): break

            #
            # parse lines, setting state, and emit complete records on disk/span-edges
            #
            current_pd = None
            current_span = None
            current_pd_device_id = None
            current_pd_slot_number = None
            current_pd_enclosure_device_id = None

            def emit(volume, span, unit, device):
                #print 'span:', span, ', spandev:', unit, ', device:', device
                if device in pd_to_ld:
                    raise Exception("physical-device is used by multiple volumes?")
                pd_to_ld[device] = {'ld': volume, 'span': span, 'unit': unit}

            for line in lines:
                if line.startswith('Span: '):
                    span_id = line.split(' ')[1]
                    if current_span:
                        emit(volume_id, current_span, current_pd, current_pd_device_id)
                        current_pd = None
                    current_span = span_id
                elif line.startswith('PD: '):
                    pd_id = line.split(' ')[1]
                    if current_pd:
                        emit(volume_id, current_span, current_pd, current_pd_device_id)
                    current_pd = pd_id
                elif line.startswith('Enclosure Device ID: '):
                    enc = line[21:].strip()
                    if enc == 'N/A': enc = ''
                    current_pd_enclosure_device_id = enc
                elif line.startswith('Slot Number: '):
                    current_pd_slot_number = line[13:]
                elif line.startswith('Device Id: '):
                    current_pd_device_id = line[11:]
            #endfor lines
            if current_pd:
                emit(volume_id, current_span, current_pd, current_pd_device_id)

        #endfor chunks
        if len(ldmap) != total_volumes:
            raise Exception("get_ldpd_map chunks did not match the indicated volume count")

        return ldmap, pd_to_ld

    #enddef get_ldpd_info


    def get_AdpAllInfo(self):
        adapter_details = {}
        config_details = {}

        l = self.megarun(['-AdpAllInfo'])
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
            adapter_details[ m[l] ] = r


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
            adapter_details[ m[l] ] = r


        # chunk[3] has the list of raw sas ports and their sas addresses
        portlines = chunks[3].strip().split("\n")
        portlines.pop(0) # 'Number of Backend Port: 8'
        portlines.pop(0) # 'Port  :  Address'
        adapter_details['portlist'] = {}
        for s in portlines:
            parts = re.split(r"\s+",s,2) # split on whitespace, "0        1221000000000000"
            l = parts[0]
            r = parts[1]
            adapter_details['portlist'][l] = r

        adapter_details['portcount'] = len(adapter_details['portlist'])


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
            adapter_details[key] = xform(r)



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
            config_details[key] = xform(r)


        #----------------------------------------------------------------
        # i will ignore everything here except for the raid level list
        # this also assumes that the first line of this block is the RAID Levels Supported: line
        l,r = megasplit(sections['Capabilities'][0])
        adapter_details['raidlevels'] = r.split(", ")


        #----------------------------------------------------------------
        # assume first line is 'ecc bucket count'
        l,r = megasplit(sections['Status'][0])
        adapter_details['ecc_bucket_count'] = int(r)


        #----------------------------------------------------------------
        # this section could be converted into an array of bools, and justkeep the original text...
        # i will ignore it for now, as well as VD and PD operations


        #----------------------------------------------------------------
        for l,r in ( megasplit(s) for s in sections['Error Counters'] if s != '' ):
            if   l == 'Memory Correctable Errors':   config_details['memory_errors_correctable'] = decode_int(r)
            elif l == 'Memory Uncorrectable Errors': config_details['memory_errors_uncorrectable'] = decode_int(r)
            else:
                raise NameError("unhandled adapter attribute '%s'='%s'"%(l,r))

        return adapter_details, config_details


    def get_LDInfo(self, target_id):

        #
        # LDInfo needs to be passed a target_id, not an index.
        #
        lines = self.megarun(['-LDInfo','-L'+str(target_id)])
        lines.pop(0) #''
        lines.pop(0) #''
        lines.pop(0) #'Adapter 0 -- Virtual Drive Information:'
        lines.pop(0) #'Virtual Drive: 0 (Target Id: 0)'

        a = {}
        for l,r in ( megasplit(l) for l in lines if l != '' ):
            a['id'] = target_id #ldid
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

        return a


    def get_event_markers(self):
        lines = self.megarun(['-AdpEventLog','-GetEventLogInfo'])
        lines.pop(0) # ''
        lines.pop(0) # 'Adapter #0'
        lines.pop(0) # ''

        lines.pop() # ''
        str = lines.pop() # 'Success in AdpEventLog'
        if str != 'Success in AdpEventLog':
            raise Exception('expected Success in AdpEventLog')
        lines.pop() # ''

        # newest, oldest, clear, shutdown, reboot
        # 'Newest Seqnum: 0xabcdabcd'  =>  {'newest' : int(abcdabcd,16)}
        markers = {}
        for line in lines:
            match = re.match(r"(\w+) Seqnum: 0x([0-9a-f]+)", line)
            if match:
                name, hex32 = match.groups()
                markers[name.lower()] = int(hex32, 16)

        return markers['newest'], markers['clear']

    def get_PDList_raw(self):

        lines = self.megarun(['-PDList'])
        pdlist = []

        a = {}
        for line in lines:
            if ':' not in line: continue

            left, right = megasplit(line)

            if left == 'Enclosure Device ID':
                if a:
                    pdlist.append(a)
                    a = {}

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
            if line.startswith('Inquiry Data'):
                a['Inquiry Data'] = line[14:]
            else:
                a[left] = right

        #endfor lines
        if a:
            pdlist.append(a)

        return pdlist


    def get_rebuild_progress(self, slot):
        lines = self.megarun(['-PDRbld','-ShowProg','-PhysDrv',"[:"+str(slot)+"]"])
        # complete: ['                                     ', 'Device(Encl-N/A Slot-2) is not in rebuild process', '']
        res = lines[1]
        if res.endswith('is not in rebuild process'):
            return 100,0

        # forgot to add an example of the in-progress output :(
        blah = res.split(' ')
        pct = blah[10][:-1]
        minutes = int(blah[12])
        return pct, minutes


    def get_PDList(self):

        pdidx = {}
        pdinfo = []
        for pd in self.get_PDList_raw():

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
                pct, elapsed = cls.get_rebuild_progress(a['slot'])
                a['rebuild_pct'] = pct
                a['rebuild_elapsed'] = elapsed

            pdinfo.append(a)
            pdidx[ (a['slot'],a['device'],) ] = a

        #endfor raw pdlist
        return pdinfo, pdidx

    def dump_events_since_clear(self, filename):
        self.megarun(['-AdpEventLog', '-GetEvents', '-f', filename])

    def dump_recent_events(self, filename, limit):
        self.megarun(['-AdpEventLog', '-GetLatest', str(limit), '-f', filename])

    """
    def clear_events(self):
        self.megarun(['-AdpEventLog', '-Clear'])
    """

    def dump_events_deleted(self, filename):
        self.megarun(['-AdpEventLog', '-IncludeDeleted', '-f', filename])


"""
setting the time
-AdpGetTime
-AdpSetTime yyyymmdd hh:mm:ss

from shell:
    megacli -AdpSetTime `date -u "+%Y%m%d %T"` -a0
"""

