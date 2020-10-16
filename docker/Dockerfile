FROM centos:latest
LABEL maintainer="Denis O. Pavlov pavlovdo@gmail.com"

RUN yum update -y && yum install -y \ 
    cronie \
    epel-release \ 
    python36

COPY *.py requirements.txt /etc/zabbix/externalscripts/pystormon/
WORKDIR /etc/zabbix/externalscripts/pystormon

RUN pip3.6 install -r requirements.txt 

ENV TZ=Europe/Moscow
RUN ln -fs /usr/share/zoneinfo/$TZ /etc/localtime

RUN echo "00 */1 * * * /etc/zabbix/externalscripts/pystormon/storage_objects_discovery.py" > /tmp/crontab && \
    echo "*/5 * * * * /etc/zabbix/externalscripts/pystormon/storage_objects_status.py" >> /tmp/crontab && \
    echo "*/1 * * * * /etc/zabbix/externalscripts/pystormon/storage_perfomance.py" >> /tmp/crontab && \
    crontab /tmp/crontab && rm /tmp/crontab

CMD ["/usr/sbin/crond","-n"]
