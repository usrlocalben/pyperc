
MEGA_EVENT_CODES = {
    0: '0:Firmware initialization started',
    1: '0:Firmware version',
    4: '0:Configuration cleared',
    7: '0:Alarm disabled by user',
    8: '0:Alarm enabled by user',
    9: '0:Background initializaton rate changed', # 'Background initialization rate changed to 100%'
    12: '0:Cache data recovered successfully',
    14: '0:Consistency Check rate changed', # 'Consistency Check rate changed to 40%'
    16: '0:Factory defaults restored',
    21: '0:Flashing image',
    22: '0:Flash of new firmware image(s)complete',
    29: '0:Hibernate command received from host',
    30: '0:Event log cleared',
    35: '0:Patrol Read complete',
    37: '0:Patrol Read Rate changed', # 'Patrol Read Rate changed to 0%'
    38: '0:Patrol Read resumed',
    39: '0:Patrol Read started',
    40: '0:Rebuild rate changed', # 'Rebuild rate changed to 100%'
    41: '0:Reconstruction rate changed', # 'Reconstruction rate changed to 40%'
    42: '0:Shutdown command received from host',
    43: '0:LogInit initial erase',
    44: '0:Time established', # 'Time established as mm/dd/yy hh:mm:ss; (NN seconds since power on)'
    47: '0:Background initialization corrected medium error', # 'Background Initialization corrected medium error (VD 00/0 at 174442, PD 03(e0xff/s3) at 174442)'
    48: '0:Background Initialization completed on VD', # 'Background Initialization completed on VD 00/0'
    51: '2:Background Initialization failed on VD', # 'Background Initialization failed on VD 00/0'
    53: '0:Background initialization started on VD', # 'Background Initialization started on VD 00/0'
    54: '0:Policy change on VD', # 'Policy change on VD 00/0 to [ID=00,dcp=61,ccp=60,ap=0,dc=0,dbgi=0] from [ID=00,dcp=61,ccp=61,ap=0,dc=0,dbgi=0]'
    57: '0:Consistency Check corrected medium error on VD', # 'Consistency Check corrected medium error (VD 00/0 at 5e11fa31, PD 15(e0xfc/s5) at 5e11fa31)'
    58: '0:Consistency Check done on VD', # 'Consistency Check done on VD 00/0'
    59: '0:Consistency Check done with corrections on VD', # 'Consistency Check done with corrections on VD 00/0, (corrections=1)'
    63: '0:Consistency Check found inconsistent parity on VD', # 'Consistency Check found inconsistent parity on VD 00/0 at strip 167c8'
    66: '0:Consistency Check started on VD', # 'Consistency Check started on VD 00/0'
    70: '0:Fast initialization started on VD',
    72: '0:Initialization complete on VD',
    73: '0:VD Properties updated', # 'VD 00/0 Properties updated to [ID=00,dcp=61,ccp=01,ap=0,dc=0,dbgi=0]'
    81: '0:State change on VD', # 'State change on VD 00/0 from OPTIMAL(3) to DEGRADED(2)'
    87: '1:Error on PD', # 'Error on PD 02(e0xff/s2) (Error 02)'
    91: '0:Inserted: Encl PD',
    93: '0:Patrol Read corrected medium error on PD', # 'Patrol Read corrected medium error on PD 06(e0xff/s6) at 1aea541'
    96: '1:Predictive failure', # 'Predictive failure: PD 02(e0xff/s2)'
    97: '3:Puncturing bad block on PD', # 'Puncturing bad block on PD 03(e0xff/s3) at 136ac01'
    98: '0:Rebuild aborted by user on PD', # 'Rebuild aborted by user on PD 02(e0xff/s2)'
    99: '0:Rebuild complete on VD', # 'Rebuild complete on VD 00/0'
    100: '0:Rebuild complete on PD', # 'Rebuild complete on PD 00(e0xff/s0)'
    101: '2:Rebuild failed on PD due to source drive error', # 'Rebuild failed on PD 03(e0xff/s3) due to source drive error'
    102: '2:Rebuild failed on PD due to target drive error', # 'Rebuild failed on PD 00(e0xff/s0) due to target drive error'
    104: '1:Rebuild resumed on PD', # 'Rebuild resumed on PD 01(e0xff/s1)'
    106: '0:Rebuild automatically started on PD', # 'Rebuild automatically started on PD 03(e0xff/s3)'
    109: '3:Unrecoverable medium error during rebuild on PD', # 'Unrecoverable medium error during rebuild on PD 02(e0xff/s2) at 136a980'
    110: '0:Corrected medium error during recovery on PD', # 'Corrected medium error during recovery on PD 15(e0xfc/s5) at 6e6123a7'
    112: '1:Removed PD', # 'Removed: PD 03(e0xff/s3)'
    113: '0:Unexpected sense', # 'Unexpected sense: PD 02(e0xff/s2) Path 1a7d0072147d, CDB: 03 00 00 00 40 00, Sense: 0/5d/10'
    114: '0:State change on PD', # 'State change on PD 00(e0x20/s0) from ONLINE(18) to UNCONFIGURED_GOOD(0)'
    120: '2:SAS topology error: Unaddressable device',
    132: '0:Dedicated Hot Spare created on PD', # 'Dedicated Hot Spare created on PD 18(e0xfc/s6) (ded,ac=1)'
    135: '0:Global Hot Spare created on PD', # 'Global Hot Spare created on PD 04(e0xff/s4) (global,rev)'
    138: '0:Created VD', # 'Created VD 00/0'
    139: '0:Deleted VD',
    141: '0:Battery Present',
    142: '1:Battery Not Present',
    143: '0:New Battery Detected',
    144: '0:Battery has been replaced',
    147: '0:Battery started charging',
    148: '2:Battery is discharging',
    149: '0:Battery temperature is normal',
    150: '3:Battery needs replacement - SOH Bad',
    151: '1:Battery relearn started',
    152: '1:Battery relearn in progress',
    153: '0:Battery relearn completed',
    155: '0:Battery relearn pending: Battery is under charge',
    157: '0:Battery relearn will start in 4 days',
    158: '0:Battery relearn will start in 2 day',
    159: '0:Battery relearn will start in 1 day',
    160: '0:Battery relearn will start in 5 hours',
    161: '1:Battery removed',
    162: '1:Current capacity of the battery is below threshold',
    163: '0:Current capacity of the battery is above threshold',
    164: '0:Enclosure (SES) discovered',
    194: '0:BBU enabled; changing WT virtual disks to WB',
    195: '1:BBU disabled; changing WB virtual disks to WT',
    215: '0:DMA test completed 516 passes successfully', # is this always 516 ?
    217: '0:Self check diagnostics completed',
    218: '0:Foreign Configuration Detected',
    219: '2:Foreign Configuration Imported',
    220: '0:Foreign Configuration Cleared',
    227: '0:Controller Hot Plug detected',
    229: '0:Disk test cannot start. No qualifying disks found',
    236: '1:PD is not a certified drive', # 'PD 03(e0xff/s3) is not a certified drive'
    237: '0:Dirty cache data discarded by user',
    238: '1:PDs missing from configuration at boot',
    240: '1:VDs missing at boot', # 'VDs missing at boot: 00'
    241: '1:Previous configuration completely missing at boot',
    242: '0:Battery charge complete',
    247: '0:Inserted: PD', # long PD data
    248: '0:Removed PD', # 'Removed: PD 03(e0xff/s3) Info: enclPd=ffff, scsiType=0, portMap=03, sasAddr=1221000003000000,0000000000000000'
    249: '0:VD is now OPTIMAL', # 'VD 00/0 is now OPTIMAL'
    250: '1:VD is now PARTIALLY DEGRADED', # 'VD 00/0 is now PARTIALLY DEGRADED'
    251: '2:VD is now DEGRADED', # 'VD 00/0 is now DEGRADED'
    252: '3:VD is now OFFLINE', # 'VD 00/0 is now OFFLINE'
    257: '1:PD missing', # 'PD missing: SasAddr=0x0, ArrayRef=0, RowIndex=0x7, EnclPd=0xff, Slot=0.'

    261: '0:Package version',
    266: '0:Board Revision', #???

    267: '1:Command timeout on PD', # 'Command timeout on PD 00(e0xff/s0) Path 1221000000000000, CDB: 28 00 18 fa ad 00 00 00 80 00'
    268: '1:PD Reset', # 'PD 00(e0xff/s0) Path 1221000000000000 reset (Type 03)'

    278: '0:CopyBack complete on PD', # 'CopyBack complete on PD 03(e0xff/s3) from PD 04(e0xff/s4)'
    280: '0:CopyBack resumed on PD', # 'CopyBack resumed on PD 03(e0xff/s3) from PD 04(e0xff/s4)'
    281: '0:CopyBack automatically started on PD', # 'CopyBack automatically started on PD 03(e0xff/s3) from PD 04(e0xff/s4)'
    286: '0:Controller hardware revision ID (0x0)', # ????
    303: '2:Controller properties changed',
}

