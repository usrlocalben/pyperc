
import os
import re


def megaraid_devs():

    def find_megaraid_devices():
        """scan sysfs for devices that use the megaraid_sas driver/module"""
        has_proc_name = (item for item in os.walk('/sys/devices/') if 'proc_name' in item[2])
        for item in has_proc_name:
            fn = item[0] + '/proc_name'
            with open(fn, 'r') as fd:
                driver = fd.read().strip()
            if driver == 'megaraid_sas':
                yield item[0]

    # raise if it is ambiguous
    devices = list(find_megaraid_devices())
    if not devices:
        return
        #raise Exception("could not find megaraid_sas device in sysfs")
    if len(devices) > 1:
        raise Exception("multiple megaraid_sas devices found")

    megapath = devices[0]

    # ['target3:2:0', 'target3:2:1', ...]
    target_strings = [item for item in os.listdir(megapath + '/device/') if item.startswith('target')]

    def sys_blocks():
        for devname in os.listdir('/sys/block/'):
            yield devname, os.readlink('/sys/block/' + devname)
   
    # filter /sys/block/ looking for any megaraid target strings
    mega_blocks = (item for item in sys_blocks() if any(target in item[1] for '/'+target+'/' in target_strings))

    # parse what remains and output
    for dev, path in mega_blocks:
        pathparts = path.split('/')
        scsi_address = pathparts[-3]
        host, bus, target, lun = scsi_address.split(':')
        yield dev, host, bus, target, lun


def proc_partitions():
    with open('/proc/partitions', 'r') as fd:
        for line in fd:
            match = re.match(r"\W*([0-9]+)\W+([0-9]+)\W+([0-9]+)\W+(.*)$", line)
            if match:
                major, minor, blocks, name = match.groups()
                yield int(major), int(minor), int(blocks), name


# garbage... any number of things could go wrong here
def get_partitions(dev):
    plst = list(proc_partitions())

    part = [item for item in plst if item[3] == dev]
    if not part:
        return
    
    yield part[0]

    pnum = 1
    while part:
        part = [item for item in plst if item[3] == dev + str(pnum)]
        if part:
            yield part[0]
        pnum += 1

