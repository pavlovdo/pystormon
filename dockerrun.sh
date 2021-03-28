#!/bin/bash

readonly PROJECT=pystormon
readonly CONFIG_DIR=/etc/zabbix/externalscripts/$PROJECT/conf.d
readonly DATA_DIR=/var/tmp/$PROJECT

message="\nRunning of container from image $PROJECT with name $PROJECT and mounting $CONFIG_DIR':'$CONFIG_DIR':ro
and $DATA_DIR:$DATA_DIR"

docker run --detach --tty --name "$PROJECT" --restart=always --volume "$CONFIG_DIR":"$CONFIG_DIR":ro "$PROJECT" \
--volume "$DATA_DIR":"$DATA_DIR"
echo -e "${message}"
