#!/bin/bash

readonly PROJECT=pystormon
readonly CONFIG_DIR=/etc/zabbix/externalscripts/$PROJECT/conf.d

message="\nRunning of container from image $PROJECT with name $PROJECT and mounting $CONFIG_DIR':'$CONFIG_DIR':ro"

docker run --detach --tty --name "$PROJECT" --restart=always --volume "$CONFIG_DIR":"$CONFIG_DIR":ro "$PROJECT"
echo -e "${message}"
