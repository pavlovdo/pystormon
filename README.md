Description
===========
Zabbix Storage Monitoring through CIM/WBEM

Tested with IBM Storwize


Requirements
============

python >= 3.4

python module py-zabbix - for sending traps to zabbix

python module pywbem (tested with version 0.12.0) - for connect and get information from storage through CIM/WBEM

zabbix-server (tested with versions 3.4-4.4)


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

3) Clone pystormon repo to directory /etc/zabbix/externalscripts of monitoring server;

4) Change example configuration files pystormon.conf: login, password, address of zabbix_server;

5) Change example configuration files devices.conf: IP and names of storages;

6) Give and check network access from monitoring server to storage management network CIM/WBEM port (TCP/5989);

7) Import Template Storage Pystormon.xml to Zabbix;

8) Create your storage hosts in Zabbix and link Template Storage Pystormon to them.
In host configuration set parameters "Host name" and "IP address" for Agent Interface.
Use the same hostname as in the file devices.conf, storwize.example.com for example.

9) Install Python 3 and pip3 if it is not installed;

10) Install required python modules:
```
pip3 install -r requirements.txt
```

11) Create cron jobs for zabbix trappers:
```
echo "00 */1 * * *  /etc/zabbix/externalscripts/pystormon/storage_discovery.py" > /tmp/crontab && \
echo "*/1 * * * *   /etc/zabbix/externalscripts/pystormon/storage_perfomance.py" >> /tmp/crontab && \
echo "*/5 * * * *   /etc/zabbix/externalscripts/pystormon/storage_status.py" >> /tmp/crontab && \
crontab /tmp/crontab && rm /tmp/crontab
```

Tested
======
Storwize v3700, v5010, v5030, v7000
Zabbix 3.4, 4.0, 4.2, 4.4

Related Links
=============
http://pywbem.github.io/pywbem/

https://github.com/adubkov/py-zabbix

https://www.snia.org/forums/smi/knowledge/smis-getting-started/smi_architecture

https://www.ibm.com/support/knowledgecenter/STHGUJ_8.3.1/com.ibm.storwize.tb5.831.doc/svc_cim_main.html
