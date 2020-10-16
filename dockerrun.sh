#!/bin/bash

readonly PROJECT=pystormon
readonly CONFIG_DIR=/etc/zabbix/externalscripts/$PROJECT
readonly CONTAINER_OS=centos

message="\nRunning of container from image $CONTAINER_OS:$PROJECT with mounting $CONFIG_DIR':'$CONFIG_DIR':ro"

docker run -d -t --restart=always -v "$CONFIG_DIR":"$CONFIG_DIR":ro "$CONTAINER_OS":"$PROJECT"
echo -e "${message}"
