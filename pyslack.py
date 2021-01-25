#!/usr/bin/env python3

# Python module for send alarms about exceptions to slack channel

def slack_post(slack_hook, message, hostname, icon_emoji=':snake:'):

    import os
    import requests
    import sys

    requests.post(slack_hook, json={'username': os.uname()[1],
                                    'icon_emoji': icon_emoji,
                                    'text': 'ERROR in: \"' +
                                    str(sys.argv[0]) + ', ' + hostname + ', '
                                    + '\"\n' + message})
