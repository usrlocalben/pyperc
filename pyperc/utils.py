
import os
import re
from datetime import datetime

def megasplit(line):
    mid = line.index(':')
    left = line[0:mid].strip()
    right = line[mid+1:].strip()
    return left, right

MEGADATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
def from_megadate(val):
    return datetime.strptime(val, MEGADATE_FORMAT)
def to_megadate(val):
    return val.strftime(MEGADATE_FORMAT)

def rematch(pattern, data):
    matches = re.match(pattern, data)
    if matches:
        yield matches

def maybe_unlink(fname):
#    try:
    os.unlink(fname)
#    except OSError:
#        pass

