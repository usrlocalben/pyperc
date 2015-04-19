#!/usr/bin/env python2.7
"""
ntp query notes:
http://blog.mattcrampton.com/post/88291892461/query-an-ntp-server-from-python
http://souptonuts.sourceforge.net/code/queryTimeServer.c.html
http://stackoverflow.com/questions/8805832/number-of-seconds-from-1st-january-1900-to-start-of-unix-epoch
"""

import struct
from datetime import datetime
from socket import socket, AF_INET, SOCK_DGRAM, timeout

NTP_PORT = 123
BUFFER_SIZE = 1024
TIME1970 = 2208988800L # 1970-01-01 00:00:00

# "20150419 21:51:00"
def megacli_strftime(val):
    return val.strftime("%Y%m%d %H:%M:%S")


def query_ntp(host='127.0.0.1', timeout=5):
    address = (host, NTP_PORT)

    request = '\x1b' + (47 * '\0')

    client = socket(AF_INET, SOCK_DGRAM)
    if timeout:
        client.settimeout(timeout)
    client.sendto(request, address)
    response, address = client.recvfrom(BUFFER_SIZE)

    data = struct.unpack('!12I', response)
    utc_timestamp = data[10] - TIME1970
    stratum = (data[0] >> 16) & 0xff

    return stratum, datetime.utcfromtimestamp(utc_timestamp)


if __name__ == '__main__':
    try:
        strat, dt = query_ntp()
    except timeout:
        print 'request timed out.'
    else:
        print 'stratum:', strat
        print 'datetime:', dt
        print 'to megacli:', megacli_strftime(dt)

