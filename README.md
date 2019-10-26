Description
===========
Zabbix Storage Monitoring through CIM/WBEM

Tested with IBM Storwize


Requirements
============

python >= 3.4

python module py-zabbix - for sending traps to zabbix

python module pywbem (tested with version 0.12.0) - for connect and get information from storage through CIM/WBEM

zabbix-server (tested with version 3.4)


Installation
============
1) Give access to storage statistic and parameters for monitoring user. For collect statistic under user zabbix from IBM Storwize:
```
chuser -usergrp RestrictedAdmin zabbix
```

2) Tune statistic collection interval. For collect statistic every minute from IBM Storwize:

```
startstats -interval 1
```

3) Clone pystormon repo to directory /etc/zabbix/externalscripts of server with access to storage management network;

4) Import Template Storage Pystormon.xml to Zabbix and link template with storage objects in Zabbix;

5) Change example configuration files: login, password, address of zabbix_server, IP and name of storage, etc.

6) Install Python 3 and pip3 if it is not installed;

7) Install required python modules:
```
pip3 install -r requirements.txt
```

8) Create cron jobs for zabbix trappers:
```
echo "00 */1 * * *  /etc/zabbix/externalscripts/pystormon/storage_discovery.py" > /tmp/crontab && \
echo "*/1 * * * *   /etc/zabbix/externalscripts/pystormon/storage_perfomance.py" >> /tmp/crontab && \
echo "*/5 * * * *   /etc/zabbix/externalscripts/pystormon/storage_status.py" >> /tmp/crontab && \
crontab /tmp/crontab && rm /tmp/crontab
```

Tested
======
Storwize v3700, v5010, v5030, v7000


Related Links
=============
http://pywbem.github.io/pywbem/

https://github.com/adubkov/py-zabbix

https://www.snia.org/forums/smi/knowledge/smis-getting-started/smi_architecture

https://www.ibm.com/support/knowledgecenter/STLM5A/com.ibm.storwize.v3700.710.doc/svc_conceptsovr_21pb0e.html

https://www.ibm.com/support/knowledgecenter/STHGUJ/com.ibm.storwize.v5000.710.doc/svc_conceptsmaptocimconcepts_3skacv.html
