# Onbox Assistant

## Introduction

Have you ever found yourself configuring a device via TELNET or SSH, when you get distracted, lose focus and enter a command that causes you to lose connectivity? If so, you've probably wished there was some way to go back in time - a way to undo your mistake.  

The following script leverages the capabilities of Cisco IOS XE and the Guest Shell container to run a Python script on the device to accomplish just that. Think of it as our very OnBox Assistant and virtual time traveler.

For this demonstration I am using the Catalyst 9300 switch (C9300-24U) running IOS-XE Software Version 16.06.01.


## How does it work?

We are going to check for network connectivity by pinging the default gateway of the switches management interface.

Here are the scenarios:
 
* The default gateway **IS** reachable. 
 - **Actions:** 
 
      - Check if a configuration change has been made by comparing the running-config with the startup-config
           - If the network is **UP** and a configuration change was **NOT DETECTED**. 
               - Sleep for 20 seconds and test for connectivity.
           - If the network is **UP** and a configuration change was **DETECTED**. 
               - Send a notification of the configuration change to Cisco Spark.
               - Sleep for 20 seconds and test for connectivity.

* The default gateway **IS NOT** reachable. 
 - **Actions:** 
 
     - Check if a configuration change has been made by comparing the running-config with the startup-config 

       - If the network is **DOWN** and a configuration change was **NOT DETECTED** no action is taken. 
        > _This prevents a configuration rollback from occurring if connectivity is lost due to a change or network event on an upstream device._

       - If a configuration change has occurred, it can be inferred that the configuration change cause the loss of connectivity. The device configuration will be rolled back to the startup-config. 
 

## Logical Flowchart
![alt text][logo]

[logo]: https://github.com/clintmann/onbox_assistant/blob/master/FlowChart-config_rollback.gif "Logic Flowchart"


## Where do I start?

**1) Configure your management interface**

This is the interface our script will use for network access - more on that a little later.

```
CDM-Cat9300# config t
Enter configuration commands, one per line.  End with CNTL/Z.

CDM-Cat9300(config)# interface GigabitEthernet0/0

CDM-Cat9300(config)# ip address <your management ip> <subnet mask>
```

**2) Enable IOx Services**

In order to host our Python script in the Guest Shell container, we must first enable the IOx services. IOx is a framework developed by Cisco that provides the capability to host applications on the network device. 


```
CDM-Cat9300#config t
Enter configuration commands, one per line.  End with CNTL/Z.

CDM-Cat9300(config)# iox

DM-Cat9300(config)# exit

CDM-Cat9300# show iox-service 

IOx Infrastructure Summary:
---------------------------
IOx service (CAF)    : Running 
IOx service (HA)     : Running 
IOx service (IOxman) : Running 
Libvirtd             : Running 
``` 
IOx must be enabled and running before moving on to the next step. 

**3) Start the Guest Shell container**

Guest Shell is a virtualized Linux-based container environment (LXC) where we will run our script. 

```
CDM-Cat9300# guestshell enable
Management Interface will be selected if configured
Please wait for completion
Guestshell enabled successfully
```
Note:
Guest Shell on the Catalyst 9300 at this time only permits network access via the management interface, so if you haven't configure your management interface yet, now is the time to do so. 

Front Panel networking - or access to the network via ports other than the management interface is not currently supported in the Catalyst 9300 or Catalyst 9500 series switches at this time. 

**4) Start Bash shell to access Guest Shell**

Inside Guest Shell is were were going to set up everything needed for our script to run. 

```
CDM-Cat9300#guestshell run bash
[guestshell@guestshell ~]$ 
```
**5) Test for network connectivity**

First ping the default gateway of your management subnet. Next, I like to also ping something public on the internet. 
If you are not able to ping successfully, you will not be able to install the python helper libraries we import in our script.

```
[guestshell@guestshell ~]$ sudo ping -c 3 <replace with your default-gateway IP>
```

**6) Configure a DNS Server**

We will utilize DNS to install our python helper libraries. 
In this example I will be using Cisco Umbrella as our DNS server. You can use your own or another Public DNS server.

```
[guestshell@guestshell ~]$ echo "nameserver 208.67.222.222" | sudo tee --append /etc/resolv.conf
```

Note: The nameserver will have to be re-entered after a switch reload

**7) Install Python helper files** 

```
[guestshell@guestshell etc]$  sudo -E pip install --upgrade pip
[guestshell@guestshell etc]$  sudo -E pip install urllib3[secure]
[guestshell@guestshell etc]$  sudo -E pip install requests
[guestshell@guestshell etc]$  sudo -E pip install pyCli
```
If you are trying to run pip from behind a proxy the above commands may have to be change to look like this. 
```
[guestshell@guestshell etc]$  sudo pip --proxy http://<replace with your proxy> install --upgrade pip
```

**8) Create a directory on the switch to store scripts**


```
[guestshell@guestshell ~]$  mkdir /bootflash/scripts
```

**9) Create a file that will contain our Python code**

```
[guestshell@guestshell ~]$  touch /bootflash/scripts/onbox_assistant_SparkAlerts.py
```

**10) Copy Python code into the file**

We will just use the default text editor vi . 

```
[guestshell@guestshell ~]$ vi /bootflash/scripts/onbox_assistant_SparkAlerts.py

```
Copy and paste script


After you paste the script into the file
> * Press ESC 
> * then : 
> * then wq 
> * Press ENTER

**11) Start the script**

```
[guestshell@guestshell ~]$ python /bootflash/scripts/onbox_assistant_SparkAlerts.py
```
> Note: If you close the terminal window, the script will cease to run. 
> 
> If you would like the script to continue to run when you disconnect from your terminal session, you can use the 'nohup' command to disassociate the script from the terminal window. 
> 
> https://en.wikipedia.org/wiki/Nohup
> 

```
[guestshell@guestshell ~]$ nohup python /bootflash/scripts/onbox_assistant_SparkAlerts.py
```

You can see if the process is running by using the following command 

```
[guestshell@guestshell ~]$ ps -ef | grep onbox_assistant_SparkAlerts.py
```
