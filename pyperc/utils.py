
from datetime import datetime

def megasplit(line):
    left, right = line.split(':', 1)
    return left.strip(), right.strip()

MEGADATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
def from_megadate(val):
    return datetime.strptime(val, MEGADATE_FORMAT)
def to_megadate(val):
    return val.strftime(MEGADATE_FORMAT)

