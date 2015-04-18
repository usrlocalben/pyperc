
from datetime import datetime

def decode_strtotime(val):
    return val

def decode_int(val):
    return int(val)

def decode_noop(val):
    return val

def decode_present(val):
    return val == 'Present'

def decode_intsec(val):
    if   val.endswith('sec'): return int(val[0:-3])
    elif val.endswith('s'):   return int(val[0:-1])
    else:
        raise ValueError("dont know how to parse intsec '%s'" % val)

def decode_intpct(val):
    if val.endswith('%'):
        return int(val[0:-1])
    else:
        raise ValueError("dont know how to parse intpct '%s'" % val)

def decode_minutes(val):
    if val.endswith(' Minutes'):
        return int(val[0:-8])
    else:
        raise ValueError("dont know how to parse minutes '%s'" % val)

RAIDLEVEL_TEXT = {
     'Primary-1, Secondary-0, RAID Level Qualifier-0': '10',
     'Primary-0, Secondary-0, RAID Level Qualifier-0': '0',
     'Primary-6, Secondary-0, RAID Level Qualifier-3': '6',
}
def decode_raidlevel(val):
    try:
        return RAIDLEVEL_TEXT[val]
    except KeyError:
        raise ValueError("unhandled raidlevel description '%s'" % val)
    
def decode_size(val):
    # 'nnn.nn GB [0xffffffff Sectors]'
    chunks = val.split(' ')
    num = chunks[0]
    unit = chunks[1]
    hex_sectors = chunks[2][3:]
    return int(hex_sectors, 16)

PD_STATE_TEXT = {
    'Failed': 'failed',
    'Offline': 'offline',
    'Rebuild': 'rebuild',
    'Online, Spun Up': 'online',
    'Unconfigured(bad)': 'unconfigured-bad',
    'Unconfigured(good), Spun Up': 'unconfigured-good',
    'Hotspare, Spun Up': 'hotspare',
}
def decode_pd_state(val):
    try:
        return PD_STATE_TEXT[val]
    except KeyError:
        raise ValueError("unhandled pd firmware state '%s'" % val)

LD_STATE_TEXT = {
    'Optimal': 'optimal',
    'Offline': 'offline',
    'Degraded': 'degraded',
    'Partially Degraded': 'degraded',
}
def decode_ld_state(val):
    try:
        return LD_STATE_TEXT[val]
    except KeyError:
        raise ValueError("unhandled ld state '%s'" % val)

def decode_cache_policy(val):
    # 'WriteBack, ReadAdaptive, Cached, No Write Cache if Bad BBU'
    xcw,xra,xce,xcbbu = val.split(', ')

    m = {'WriteThrough': 'WT', 'WriteBack': 'WB'}
    try:
        cw = m[xcw]
    except KeyError:
        raise ValueError("unhandled cache policy (write) '%s'" % xcw)

    m = {'ReadAheadNone': 'NORA', 'ReadAdaptive': 'ADRA', 'ReadAhead': 'RA'}
    try:
        cra = m[xra]
    except KeyError:
        raise ValueError("unhandled cache policy (readahead) '%s'"%(xra))

    m = {'Cached': 'Cached', 'Direct': 'Direct'}
    try:
        ce = m[xce]
    except KeyError:
        raise ValueError("unhandled cache policy (enable) '%s'"%(xce))

    m = {'No Write Cache if Bad BBU': 'NonCachedBadBBU', 'Write Cache OK if Bad BBU': 'CachedBadBBU'}
    try:
        cbbu = m[xcbbu]
    except KeyError:
        raise ValueError("unhandled cache policy (bbusafety) '%s'"%(xcbbu))

    return cw + '-' + cra + '-' + ce + '-' + cbbu

def decode_event_time(val):
    return datetime.strptime(val, '%a %b %d %H:%M:%S %Y')

def decode_stripe_size(val):
    m = {
         '16 KB'  :   16,
         '32 KB'  :   32,
         '64 KB'  :   64,
        '128 KB' :  128,
        '256 KB' :  256,
        '512 KB' :  512,
        '1.0 MB' : 1024,
    }
    try:
        return m[val]
    except KeyError:
        raise ValueError("unhandled ld stripe size '%s'" % val)

def hmem_to_int(val):
    assert isinstance(val, basestring)
    if val.endswith('MB'):
        return int(val[0:-2])
    elif val.endswith('GB'):
        return int(val[0:-2])*1024
    else:
        raise ValueError("unknown memory size '%s'" % val)

