# pyperc

megacli sucks.
let's fix that.
![Alt text](/../screenshots/screenshots/pyperc800.png?raw=true "pyPerc")

### useful pages:
http://tools.rapidsoft.de/perc/perc-cheat-sheet.html

http://wiki.hetzner.de/index.php/LSI_RAID_Controller/en

### sudoers bits
```
Cmnd_Alias MEGACLI = /usr/local/sbin/megacli
Defaults!MEGACLI !syslog, !pam_session  # avoid lots of log noise
... and ...
{{user}} ALL=(ALL) NOPASSWD: MEGACLI
```

### megacli wrapper
```
#!/bin/sh
/opt/MegaRAID/MegaCli/MegaCli64 $* -NoLog
```
