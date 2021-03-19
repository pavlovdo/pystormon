FROM centos:latest
LABEL maintainer="Denis O. Pavlov pavlovdo@gmail.com"

ARG project

RUN yum update -y && yum install -y \ 
    cronie \
    epel-release \ 
    python36

COPY *.py requirements.txt /etc/zabbix/externalscripts/${project}/
WORKDIR /etc/zabbix/externalscripts/${project}

RUN pip3.6 install -r requirements.txt 

ENV TZ=Europe/Moscow
RUN ln -fs /usr/share/zoneinfo/$TZ /etc/localtime

RUN echo "00 */1 * * * /etc/zabbix/externalscripts/pystormon/storage_objects_discovery.py 1> /proc/1/fd/1 2> /proc/1/fd/2" > /tmp/crontab && \
    echo "*/5 * * * * /etc/zabbix/externalscripts/pystormon/storage_objects_status.py 1> /proc/1/fd/1 2> /proc/1/fd/2" >> /tmp/crontab && \
    echo "*/1 * * * * /etc/zabbix/externalscripts/pystormon/storage_perfomance.py 1> /proc/1/fd/1 2> /proc/1/fd/2" >> /tmp/crontab && \
    crontab /tmp/crontab && rm /tmp/crontab

CMD ["crond","-n"]
