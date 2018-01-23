# Onbox Assistant

## Introduction

Have you ever found yourself configuring a device via TELNET or SSH, when you get distracted, lose focus and enter a command that causes you to lose connectivity? If so, you've probably wished there was some way to go back in time - a way to undo your mistake.  

The following script leverages the capabilities of Cisco IOS XE and the Guest Shell container to run a Python script on the device to accomplish just that. Think of it as our very OnBox Assistant.

For this demonstration I am using the Catalyst 9300 switch (C9300-24U) running IOS-XE Software Version 16.06.01. This script will utilize Cisco Spark for alerting. 

*What if...*  
 - I do not have a physical switch to test with? I recommend utilizing the _"IOS XE on Catalyst 9000"_   Sandbox Lab at 

    <https://developer.cisco.com/site/sandbox/>
    
    Where you will be able to reserve time and test there for FREE!

![DEVNET Sandbox][logo]

[logo]: https://github.com/clintmann/onbox_assistant/blob/master/images/DEVNET_Sandbox.gif "DEVNET Sandbox"



*What if...* 
 - I have never worked with Cisco Spark before?  No problem, check out the Learning Labs over at the Cisco DEVNET site  <https://developer.cisco.com>  to learn more on how apps utilize Cisco Spark.

     You can also find a ton of great information on the Cisco Spark for Developers site at <https://developer.ciscospark.com/>


## How does the script work?

We are going to check for network connectivity by pinging the default gateway of the switches management interface. You can add functions to test for other requirements if you would like. 

Here are the scenarios:
 
* The default gateway **IS** reachable. 
 - **Actions:** 
 
      - Check if a configuration change has been made by comparing the running-config with the startup-config
           - If the network is **UP** and a configuration change was **NOT DETECTED**. 
               - No action taken.
           - If the network is **UP** and a configuration change was **DETECTED**. 
               - Send a notification of the configuration change to Cisco Spark.

* The default gateway **IS NOT** reachable. 
 - **Actions:** 
 
     - Check if a configuration change has been made by comparing the running-config with the startup-config 
          - If the network is **DOWN** and a configuration change was **NOT DETECTED** 
              - No action is taken. 
        > _This prevents a configuration rollback from occurring if connectivity is lost due to a change or network event on an upstream device._
          - If the network is **DOWN** and a configuration change was **DETECTED** 
              - The device configuration will be rolled back to the startup-config. It can be inferred that the configuration change cause the loss of connectivity. 
 

## Logical Flowchart
![LOGIC FLOWCHART][logo2]

[logo2]: https://github.com/clintmann/onbox_assistant/blob/master/images/OnBox_Flowchart.gif "Logic Flowchart"


## Where do I start?

**1) Configure your management interface**

###### _This step is not necessary if your using the Sandbox_

This is the interface our script will use for network access - more on that a little later.

```
Cat9300# config t
Enter configuration commands, one per line.  End with CNTL/Z.

Cat9300(config)# interface GigabitEthernet0/0

Cat9300(config)# ip address <your management ip> <subnet mask>
```

**2) Enable IOx Services**

###### _This step is not necessary if your using the Sandbox_

In order to host our Python script in the Guest Shell container, we must first enable the IOx services. IOx is a framework developed by Cisco that provides the capability to host applications on the network device. 


```
Cat9300# config t
Enter configuration commands, one per line.  End with CNTL/Z.

Cat9300(config)# iox

Cat9300(config)# exit

Cat9300# show iox-service 

IOx Infrastructure Summary:
---------------------------
IOx service (CAF)    : Running 
IOx service (HA)     : Running 
IOx service (IOxman) : Running 
Libvirtd             : Running 
``` 
IOx must be enabled and running before moving on to the next step. 

**3) Start the Guest Shell container**

###### _This step is not necessary if your using the Sandbox_

Guest Shell is a virtualized Linux-based container environment (LXC) where we will run our script. 

```
Cat9300# guestshell enable
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
Cat9300# guestshell run bash
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

**11) Trigger the script**

```
Cat9300# config t
Enter configuration commands, one per line.  End with CNTL/Z.

Cat9300(config)# event manager applet GUESTSHELL-RUN-ONBOX_ASSIST_APP
Cat9300(config-applet)#  event cli pattern "^conf[a-z]*\st" sync no skip no
Cat9300(config-applet)#  action 0.0 cli command "enable"
Cat9300(config-applet)#  action 1.0 cli command "guestshell run python /bootflash/scripts/onbox_assistant_SparkAlerts.py"
Cat9300(config-applet)#  action 2.0 syslog msg "CONFIG TRIGGER : Started onbox_assistant_SparkAlerts.py  in Guestshell"
```

**12) Terminate the script**

```
Cat9300# config t
Enter configuration commands, one per line.  End with CNTL/Z.

Cat9300(config)# event manager applet GUESTSHELL-KILL-ONBOX_ASSIST_APP
Cat9300(config-applet)#  event syslog pattern "%SYS-5-CONFIG_I: Configured from"
Cat9300(config-applet)#  action 1.0 cli command "enable"
Cat9300(config-applet)#  action 2.0 cli command "guestshell run pkill -f  /bootflash/scripts/onbox_assistant_SparkAlerts.py"
Cat9300(config-applet)#  action 3.0 syslog msg "CONFIG TRIGGER : Killed OnBoxAssist_SparkAlert.py  in Guestshell"
```

