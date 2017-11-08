import os
import sys
import re
import time
import requests
import json
from cli import cli, clip, execute, executep, configure, configurep
from ciscosparkapi import CiscoSparkAPI, SparkApiError

gw_ip = "<gateway IP>"
tropoToken = "<tropo token>"
apistring = "https://api.tropo.com/1.0/sessions"
phNum = "<phone number NO dashes>"


def pingTest(mgmt_ip):
    response = os.system("sudo ping -c 3 " + str(mgmt_ip))
    # and then check the response...
    if response == 0:
        # mgmt_ip_address is up
        connected = True
    else:
        # mgmt_ip_address is down!
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


def rollBack():
    execute("configure replace nvram:startup-config force")


def sparkAlert(token, email, message2):
    api = CiscoSparkAPI(access_token=token)
    api.messages.create(toPersonEmail=email, markdown=message2)


def txtAlert(apistring, tropoToken, phNum, txt_alert):
    # Set up the Headers based upon the Tropo API
    headers = {'accept': 'application/json',
               'content-type': 'application/json'}

    # Create the payload value that includes the parameters that we need to pass to the Tropo API

    payload = {'token': tropoToken, 'numberToDial': phNum,
               'alertMessage': txt_alert}

    # Post the API call to the tropo API using the payload and headers defined above
    resp = requests.post(apistring, json=payload, headers=headers)


if __name__ == '__main__':
    # Use ArgParse to retrieve command line parameters.
    from argparse import ArgumentParser

    parser = ArgumentParser("Spark Check In")
    # Retrieve the Spark Token and Destination Email
    parser.add_argument(
        "-t", "--token", help="Spark Authentication Token", required=True
    )
    # Retrieve the Spark Token and Destination Email
    parser.add_argument(
        "-e", "--email", help="Email to Send to", required=True
    )
    args = parser.parse_args()
    token = args.token
    email = args.email

    hostname = getHostname()

    latest_diff = ""  # empty to start

    try:
        while True:
            # check for diff between run and start cfg
            diff = configDiff()
            # if run and start are sync'd this will be the result of diff
            run_start_syncd = "!Contextual Config Diffs:\n"
            connected = pingTest(gw_ip)

            if connected is True:
                if diff == run_start_syncd:  # there is no difference detected
                    # no config change sleep and check again in 20 seconds
                    print "NO CHANGE DETECTED - Waiting 20 Seconds"
                    time.sleep(20)

                else:  # there is a change to the config
                    if diff != latest_diff:
                        connected = pingTest(gw_ip)
                        if connected is True:
                            print "CHANGE DETECTED - sending message to SPARKBOT"
                            message = "**Alert:** Configuration Change on host " + str(hostname) \
                                      + ": <br/>" + "<< DIFFS BETWEEN RUNNING-CONFIG AND STARTUP-CONFIG >>" \
                                      + ": <br/>" +str(diff)

                            sparkAlert(token, email, message)
                            latest_diff = diff
                        else:  # second ping test failed can sent to spark roll back
                            rollBack()
                            connected = pingTest(gw_ip)

                            while connected is False:  # config rolled back ping not back yet
                                connected = pingTest(gw_ip)

                            # ping is successful send message to spark
                            message2 = "**ROLLING BACK:** Configuration on host " + str(hostname) \
                                       + ": <br/>" + "<< DIFFS BETWEEN RUNNING-CONFIG AND STARTUP-CONFIG >>" \
                                       + ": <br/>" +str(diff)

                            txt_alert = "**ROLLING BACK:** Configuration on host " + str(hostname) \
                                        + ":" + "<< DIFFS BETWEEN RUNNING-CONFIG AND STARTUP-CONFIG >>" \
                                        + ":" + str(diff)

                            sparkAlert(token, email, message2)

                            txtAlert(apistring, tropoToken, phNum, txt_alert)

                    else:
                        #  already sent spark message don't send again
                        print "Spark message sent - write mem on switch still needed"
            else:
                # CAN NOT PING DEVICE
                rollBack()  # rollback config to startup-config

                connected = pingTest(gw_ip)  # just rolled back check for ping

                while connected is False:  # ping until device is back up
                    connected = pingTest(gw_ip)  # just rolled back check for ping

                    # ping is successful send message to spark
                    message2 = "**ROLLING BACK:** Configuration on host " + str(hostname) \
                               + ":< br / > " +" << DIFFS BETWEEN RUNNING - CONFIG AND STARTUP - CONFIG >> " \
                               + ":< br / > " +str(diff)

                    txt_alert = "**ROLLING BACK:** Configuration on host" + str(hostname) \
                                + ":" +" << DIFFS BETWEEN RUNNING - CONFIG AND STARTUP - CONFIG >> " \
                                + ":" +str(diff)

                    sparkAlert(token, email, message2)

                    txtAlert(apistring, tropoToken, phNum, txt_alert)

    except KeyboardInterrupt:  # allow user to break loop
        print "Manual break by user - CTRL-C"
