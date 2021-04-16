Description
===========
Zabbix Storage Monitoring via CIM/WBEM


Requirements
============

1) python >= 3.6

2) python module pywbem: connect and get information from storage via CIM/WBEM

3) zabbix-server (tested with versions 4.4-5.2)

4) python module py-zabbix: sending traps to zabbix


Installation
============
1) Give access to storage statistic and parameters of your storages for monitoring user. 
For collect statistic under user zabbix from IBM Storwize:
```
chuser -usergrp RestrictedAdmin zabbix
```

2) Tune statistic collection interval. For collect statistic every minute from IBM Storwize:

```
startstats -interval 1
```

3) Clone pystormon repo to directory /etc/zabbix/externalscripts of monitoring server:
```
sudo mkdir -p /etc/zabbix/externalscripts
sudo git clone https://github.com/pavlovdo/pystormon /etc/zabbix/externalscripts/pystormon
cd /etc/zabbix/externalscripts/pystormon
```

4) A) Check execute permissions for scripts:
```
ls -l *.py *.sh
```
B) If not:
```
sudo chmod +x *.py *.sh
```

5) Change example configuration files pystormon.conf: storages login/password, address of zabbix_server;

6) Change example configuration files devices.conf: IP and hostnames of storages;

7) Give and check network access from monitoring server to storage management network CIM/WBEM port (TCP/5989);

8) Check configuration and running zabbix trappers on your zabbix server or proxy:
```
### Option: StartTrappers
#       Number of pre-forked instances of trappers.
#       Trappers accept incoming connections from Zabbix sender, active agents and active proxies.
#       At least one trapper process must be running to display server availability and view queue
#       in the frontend.
#
# Mandatory: no
# Range: 0-1000
# Default:
# StartTrappers=5
```
```
# ps aux | grep trapper
zabbix    776389  0.2  0.4 2049416 111772 ?      S    дек07  63:41 /usr/sbin/zabbix_server: trapper #1 [processed data in 0.000166 sec, waiting for connection]
zabbix    776390  0.2  0.4 2049512 112016 ?      S    дек07  63:43 /usr/sbin/zabbix_server: trapper #2 [processed data in 0.000342 sec, waiting for connection]
zabbix    776391  0.2  0.4 2049452 112092 ?      S    дек07  63:12 /usr/sbin/zabbix_server: trapper #3 [processed data in 0.000301 sec, waiting for connection]
zabbix    776392  0.2  0.4 2049600 112064 ?      S    дек07  63:57 /usr/sbin/zabbix_server: trapper #4 [processed data in 0.000187 sec, waiting for connection]
zabbix    776393  0.2  0.4 2049412 111836 ?      S    дек07  63:31 /usr/sbin/zabbix_server: trapper #5 [processed data in 0.000176 sec, waiting for connection]
```

9) Import template Storage Pystormon.json to Zabbix, if use Zabbix 5.2,
and Storage Pystormon 4.4.xml (no more support) for Zabbix 4.4;

10) Create your storage hosts in Zabbix and link template Storage Pystormon to it.
In host configuration set parameters "Host name" and "IP address" for Agent Interface.
Use the same hostname as in the file devices.conf, storwize.example.com for example.

11) Further you have options: run scripts from host or run scripts from docker container.

If you want to run scripts from host:

A) Install Python 3 and pip3 if it is not installed;

B) Install required python modules:
```
pip3 install -r requirements.txt
```

C) Create cron jobs for zabbix trappers:
```
echo "00 */1 * * *  /etc/zabbix/externalscripts/pystormon/storage_objects_discovery.py 1> /dev/null" > /tmp/crontab && \
echo "*/5 * * * *   /etc/zabbix/externalscripts/pystormon/storage_objects_status.py 1> /dev/null" >> /tmp/crontab && \
echo "*/1 * * * *   /etc/zabbix/externalscripts/pystormon/storage_perfomance.py 1> /dev/null" >> /tmp/crontab && \
crontab /tmp/crontab && rm /tmp/crontab
```


If you want to run scripts from docker container:

A) Run build.sh:
```
cd /etc/zabbix/externalscripts/pystormon
./build.sh
```

B) Run dockerrun.sh;
```
./dockerrun.sh
```


Notes
======
1) You can add or remove monitoring of your storage cim classes and properties in file monitored_properties.json
and in template Storage Pystormon. Storage CIM classes maps to Zabbix discoveries, and CIM class properties maps
to Zabbix discoveries items.


2) You can change perfomance macros values in template Storage Pystormon (for Zabbix 5.2 templates);


3) For send exception alarms via slack hook to your slack channel, set parameter slack_hook in conf.d/pystormon.conf.
More details in https://api.slack.com/messaging/webhooks


4) You can print all names/values from those storage CIM classes that exist in monitored_properties.json, via script storage_cim_print.py.
It get CIM classes from monitored_properties.json and print all names/values for its.


5) If you start storage_cim_print.py and get empty values for some classes, for example classes IBMTSSVC_StorageVolume, IBMTSSVC_StorageVolumeStatistics, 
check that you create corresponding objects (VDisks in our example) on your storage;


6) You can print any storage CIM class and it property's names/values via script storage_cim_print_search.py. For that you have to create directory with your username permissions for detected_properties_file:
```
sudo mkdir /var/tmp/pystormon && sudo chown username /var/tmp/pystormon
```

And now you set search substrings via script arguments, for example:
```
/etc/zabbix/externalscripts/pystormon/storage_cim_print_search.py FC iSCSI
```

In result you get output of property's names and values of all storage CIM classes that contain word 'FC' and 'iSCSI' (case sensitive) to console and to file set by config parameter detected_properties_file (see pystormon.conf):
```
$ cat /var/tmp/pystormon/detected_properties.txt
Device: storwize.example.com CIM class: IBMTSSVC_iSCSICapabilities
Property: Caption, Value: None
 
Device: storwize1.example.com, CIM class: IBMTSSVC_iSCSICapabilities
Property: Description, Value: None
...
```


Tested
======
IBM Storwize v3700/v5010/v5030/v7000, software versions 7.8.x - 8.3.x

Zabbix 5.2


Related Links
=============
http://pywbem.github.io/pywbem/

https://www.snia.org/forums/smi/knowledge/smis-getting-started/smi_architecture

https://www.ibm.com/support/knowledgecenter/STHGUJ_8.3.1/com.ibm.storwize.tb5.831.doc/svc_cim_main.html

https://github.com/adubkov/py-zabbix

https://api.slack.com/messaging/webhooks
