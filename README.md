# pyperc

megacli sucks.
let's fix that.
![Alt text](/../screenshots/screenshots/pyperc800.png?raw=true "pyPerc")

### megacli download:

http://www.lsi.com/support/Pages/download-results.aspx?keyword=megacli

at this time, it is "MegaCLI - Linux Patch" 8.07.10


### useful pages:
http://tools.rapidsoft.de/perc/perc-cheat-sheet.html

http://wiki.hetzner.de/index.php/LSI_RAID_Controller/en


### sudoers bits
```
Cmnd_Alias MEGACLI = /opt/MegaRAID/MegaCli/MegaCli64
Defaults!MEGACLI !syslog, !pam_session  # avoid lots of log noise
... and ...
{{user}} ALL=(ALL) NOPASSWD: MEGACLI
```

