#! /usr/bin/env python
"""
OnBox Assistant
Author: Clint Mann

Illustrates the following concepts:
- Leverage the capabilities of Cisco IOS XE and the Guest Shell
  container to run a Python script on-box.

- This script will send alerts to a Spark room when configuration
  changes are made and rollback the configuration if a change causes
  a loss of network connectivity.
"""

__author__ = "Clint Mann"
__license__ = "MIT"


import os
import re
from cli import execute
from ciscosparkapi import CiscoSparkAPI, SparkApiError

gw_ip = "<GATEWAY_IP>"
token = "<TOKEN>"
email = "<EMAIL>"


def pingTest(gw_ip):
    response = os.system("sudo ping -c 3 " + str(gw_ip))
    # Check the response
    if response == 0:
        # gw_ip_address is up
        connected = True
    else:
        # gw_ip_address is down!
        connected = False

    return connected


def getHostname():
    sh_run = execute("show run | include hostname")
    list1 = sh_run.split("hostname", 1)[1]
    hostname = list1.split("!", 1)[0]


    return hostname


def configDiff():
    # Compare difference between last know good and running config
    diff_run_start = execute("show archive config differences "
                             "system:running-config nvram:startup-config")
    deleteKey = re.sub('crypto(?s)(.*)quit', '', diff_run_start)
    deleteCrypto = re.sub('crypto', '', deleteKey)
    diff = re.sub('quit', '', deleteCrypto)

    return diff


def checkNTP():
    # Check the status of NTP
    ntp = execute("show ntp status")

    if 'unsynchronized' in ntp:
        ntp_status = False
    else:
        ntp_status = True

    return ntp_status


def rollBack():
    execute("configure replace nvram:startup-config force")


def sparkAlert(token, email, message):
    api = CiscoSparkAPI(access_token=token)
    api.messages.create(toPersonEmail=email, markdown=message)


if __name__ == '__main__':

    hostname = getHostname()

    latest_diff = ""  # empty to start

    try:
        while True:
            # check for diff between run and start cfg
            diff = configDiff()

            # if run and start are sync'd this will be the result of diff
            run_start_syncd = "!Contextual Config Diffs:\n"

            connected = pingTest(gw_ip)
            #ntp = checkNTP()

            if connected is True:  # PING SUCCESSFUL
                if diff == run_start_syncd:  # there is no difference detected
                    # no config change - sleep and check again in 5 seconds
                    print "NO CHANGE DETECTED"

                else:  # there is a change to the config send it to SPARK
                    if diff != latest_diff:

                        print "CHANGE DETECTED - sending message to SPARKBOT"
                        message = "**Alert:** Configuration Change on host " + str(hostname) \
                                  + ": <br/>" + "<< DIFFS BETWEEN RUNNING-CONFIG AND STARTUP-CONFIG >>" \
                                  + ": <br/>" + str(diff)

                        sparkAlert(token, email, message)
                        latest_diff = diff

                    else:  # already sent spark message don't send again
                        print "Spark message sent - write mem on switch still needed"
            else:  # PING UNSUCCESSFUL
                # NO CONFIG CHANGE - DO NOT ROLLBACK
                if diff == run_start_syncd:  # there is no difference detected
                    # no config change sleep and check again in 20 seconds
                    print "NO CHANGE DETECTED"

                # CONFIG CHANGE DETECTED - ROLLBACK
                else:
                    rollBack()  # rollback config to startup-config

                    connected = pingTest(gw_ip)  # just rolled back check for ping

                while connected is False:  # ping until device is back up
                    connected = pingTest(gw_ip)  # just rolled back check for ping

                # ping is successful send message to spark
                message = "**ROLLING BACK:** Configuration on host " + str(hostname) \
                              + ": <br/> " + " << DIFFS BETWEEN RUNNING - CONFIG AND STARTUP - CONFIG >> " \
                              + ": <br/> " + str(diff)

                sparkAlert(token, email, message)

    except KeyboardInterrupt:  # allow user to break loop
        print "Manual break by user - CTRL-C"

