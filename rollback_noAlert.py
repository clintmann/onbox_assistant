import os
import re
import time
from cli import cli, clip, execute, executep, configure, configurep


gw_ip = "<gateway IP>"


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


if __name__ == '__main__':

    try:
        while True:
            # check for diff between run and start cfg
            diff = configDiff()
            # if run and start are sync'd this will be the result of diff
            run_start_syncd = "!Contextual Config Diffs:\n"
            connected = pingTest(gw_ip)

            if connected is True:
                # PING IS SUCCESSFUL
                if diff == run_start_syncd:  # there is no difference detected
                    # no config change sleep and check again in 20 seconds
                    print "NO CHANGE DETECTED - Waiting 20 Seconds"
                    time.sleep(20)

            else:
                # CAN NOT PING DEVICE
                rollBack()  # rollback running-config to startup-config

                connected = pingTest(gw_ip)  # just rolled back check for ping

                while connected is False:  # ping until device is back up
                    connected = pingTest(gw_ip)  # check ping after rollback

    except KeyboardInterrupt:  # allow user to break loop
        print "Manual break by user - CTRL-C"
